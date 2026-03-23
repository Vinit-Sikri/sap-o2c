
from typing import Any, Dict, List, Optional

import networkx as nx


def _node_id(node_type: str, value: Any) -> str:
    return f"{node_type}:{value}"


def _entity_value(node_id: str) -> str:
    return str(node_id).split(":", 1)[1] if ":" in str(node_id) else str(node_id)


def _find_node(G: nx.DiGraph, node_type: str, entity_id: str) -> Optional[str]:
    target = str(entity_id)
    for node, attrs in G.nodes(data=True):
        if attrs.get("type") == node_type and attrs.get("entity_id") == target:
            return node
        if node == _node_id(node_type, target):
            return node
    return None


def _path_to_dict(G: nx.DiGraph, path: List[str]) -> List[Dict[str, str]]:
    return [
        {
            "node": node,
            "type": G.nodes[node].get("type", ""),
            "id": _entity_value(node),
        }
        for node in path
    ]


def trace_order(G, order_id):
    order_node = _find_node(G, "Order", order_id)
    if not order_node:
        return {
            "found": False,
            "order_id": str(order_id),
            "path": [],
            "summary": f"Order {order_id} was not found.",
            "status": "missing",
            "insight": "The order may not exist in the loaded dataset.",
        }

    path = [order_node]
    current = order_node
    visited = {order_node}

    while True:
        successors = [nbr for nbr in G.successors(current) if nbr not in visited]
        if not successors:
            break

        next_node = next(
            (nbr for nbr in successors if G.nodes[nbr].get("type") in {"Delivery", "Invoice", "Payment"}),
            successors[0],
        )
        path.append(next_node)
        visited.add(next_node)
        current = next_node

        if G.nodes[current].get("type") == "Payment":
            break

    path_dict = _path_to_dict(G, path)
    path_types = [item["type"] for item in path_dict]

    if "Payment" in path_types:
        status = "completed"
        insight = "The order has completed the full order-to-cash cycle."
        summary = f"Order {order_id} has been delivered, invoiced, and paid."
    elif "Invoice" in path_types:
        status = "pending"
        insight = "The order has progressed well, but payment has not yet been captured."
        summary = f"Order {order_id} has been invoiced, but payment is still pending."
    elif "Delivery" in path_types:
        status = "pending"
        insight = "This may indicate a billing delay or revenue still waiting to be recognized."
        summary = f"Order {order_id} has been delivered but not invoiced yet."
    else:
        status = "missing"
        insight = "The order exists, but no downstream fulfillment or billing records were found."
        summary = f"Order {order_id} was found, but no delivery, invoice, or payment flow exists."

    return {
        "found": True,
        "order_id": str(order_id),
        "path": path_dict,
        "summary": summary,
        "status": status,
        "insight": insight,
    }


def trace_invoice(G, invoice_id: str) -> Dict[str, Any]:
    invoice_node = _find_node(G, "Invoice", invoice_id)
    if not invoice_node:
        return {
            "found": False,
            "invoice_id": str(invoice_id),
            "path": [],
            "summary": f"Invoice {invoice_id} was not found.",
            "status": "missing",
            "insight": "The invoice may not exist in the loaded dataset.",
        }

    path = [invoice_node]
    delivery_node = next(
        (nbr for nbr in G.predecessors(invoice_node) if G.nodes[nbr].get("type") == "Delivery"),
        None,
    )

    if delivery_node:
        order_node = next(
            (nbr for nbr in G.predecessors(delivery_node) if G.nodes[nbr].get("type") == "Order"),
            None,
        )
        if order_node:
            path = [order_node, delivery_node, invoice_node]
        else:
            path = [delivery_node, invoice_node]

    payment_node = next(
        (nbr for nbr in G.successors(invoice_node) if G.nodes[nbr].get("type") == "Payment"),
        None,
    )
    if payment_node:
        path.append(payment_node)

    path_dict = _path_to_dict(G, path)
    path_types = [item["type"] for item in path_dict]

    if "Payment" in path_types:
        status = "completed"
        insight = "The invoice has been settled, which supports clean revenue realization."
        summary = f"Invoice {invoice_id} has been fully paid."
    elif "Invoice" in path_types and "Delivery" in path_types:
        status = "pending"
        insight = "The invoice exists, but cash collection is still outstanding."
        summary = f"Invoice {invoice_id} exists and is waiting on payment."
    elif "Delivery" in path_types:
        status = "pending"
        insight = "The document chain is incomplete after delivery, which may point to a billing gap."
        summary = f"Invoice {invoice_id} is linked back to delivery, but payment is missing."
    else:
        status = "missing"
        insight = "No supporting upstream or downstream process records were found."
        summary = f"Invoice {invoice_id} was found, but its related flow is incomplete."

    return {
        "found": True,
        "invoice_id": str(invoice_id),
        "path": path_dict,
        "summary": summary,
        "status": status,
        "insight": insight,
    }


def find_orders_without_invoices(G) -> Dict[str, Any]:
    missing = []

    for node, attrs in G.nodes(data=True):
        if attrs.get("type") != "Order":
            continue

        has_invoice = any(
            G.nodes[desc].get("type") == "Invoice"
            for desc in nx.descendants(G, node)
        )
        if not has_invoice:
            missing.append(_entity_value(node))

    count = len(missing)
    return {
        "count": count,
        "order_ids": missing,
        "summary": (
            f"Found {count} order{'s' if count != 1 else ''} without invoices."
            if count
            else "No orders without invoices were found."
        ),
        "status": "missing" if count else "completed",
        "insight": (
            "This may indicate revenue leakage, billing delays, or orders stuck before invoicing."
            if count
            else "The order-to-invoice process looks healthy for the loaded dataset."
        ),
    }
