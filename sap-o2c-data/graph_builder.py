import pandas as pd
import os

base_path = os.path.abspath(os.path.dirname(__file__))

def load_json_folder(folder_name):
    folder_path = os.path.join(base_path, folder_name)
    files = os.listdir(folder_path)
    dfs = []

    for file in files:
        if file.endswith(".jsonl"):
            df = pd.read_json(os.path.join(folder_path, file), lines=True)
            dfs.append(df)

    return pd.concat(dfs, ignore_index=True)


# LOAD DATA
sales_order_headers = load_json_folder("sales_order_headers")
outbound_delivery_items = load_json_folder("outbound_delivery_items")
billing_document_items = load_json_folder("billing_document_items")
payments_accounts_receivable = load_json_folder("payments_accounts_receivable")

import networkx as nx

# Assumes these DataFrames already exist:
# sales_order_headers
# outbound_delivery_items
# billing_document_items
# payments_accounts_receivable

def build_sap_otc_graph(
    sales_order_headers,
    outbound_delivery_items,
    billing_document_items,
    payments_accounts_receivable,
):
    """
    Build a directed SAP Order-to-Cash graph.

    Node types:
      - Customer: soldToParty
      - Order: salesOrder
      - Delivery: deliveryDocument
      - Invoice: billingDocument
      - Payment: accountingDocument

    Edges:
      - Customer -> Order
      - Order -> Delivery
      - Delivery -> Invoice
      - Invoice -> Payment
    """

    G = nx.DiGraph()

    def node_id(node_type, value):
        # Prefix IDs so the same raw value in different entity types does not collide.
        return f"{node_type}:{value}"

    def add_nodes_from_df(df, id_col, node_type):
        if id_col not in df.columns:
            return
        values = df[id_col].dropna().astype(str).unique()
        for value in values:
            G.add_node(
                node_id(node_type, value),
                type=node_type,
                entity_id=value,
            )

    def add_edges_from_relationship(source_df, source_col, target_col, source_type, target_type, relation):
        if source_col not in source_df.columns or target_col not in source_df.columns:
            return

        rel_df = source_df[[source_col, target_col]].dropna()
        rel_df[source_col] = rel_df[source_col].astype(str)
        rel_df[target_col] = rel_df[target_col].astype(str)

        for src_val, tgt_val in rel_df[[source_col, target_col]].drop_duplicates().itertuples(index=False, name=None):
            src = node_id(source_type, src_val)
            tgt = node_id(target_type, tgt_val)

            # Ensure nodes exist even if the related entity was not present in its own dataframe.
            if src not in G:
                G.add_node(src, type=source_type, entity_id=src_val)
            if tgt not in G:
                G.add_node(tgt, type=target_type, entity_id=tgt_val)

            G.add_edge(src, tgt, relation=relation)

    # 1) Add nodes
    add_nodes_from_df(sales_order_headers, "soldToParty", "Customer")
    add_nodes_from_df(sales_order_headers, "salesOrder", "Order")
    add_nodes_from_df(outbound_delivery_items, "deliveryDocument", "Delivery")
    add_nodes_from_df(billing_document_items, "billingDocument", "Invoice")
    add_nodes_from_df(payments_accounts_receivable, "accountingDocument", "Payment")

    # 2) Add edges
    # Customer -> Order
    if {"soldToParty", "salesOrder"}.issubset(sales_order_headers.columns):
        rel_df = sales_order_headers[["soldToParty", "salesOrder"]].dropna()
        rel_df["soldToParty"] = rel_df["soldToParty"].astype(str)
        rel_df["salesOrder"] = rel_df["salesOrder"].astype(str)

        for customer_id, order_id in rel_df.drop_duplicates().itertuples(index=False, name=None):
            G.add_edge(
                node_id("Customer", customer_id),
                node_id("Order", order_id),
                relation="customer_to_order",
            )

    # Order -> Delivery via referenceSdDocument
    add_edges_from_relationship(
        outbound_delivery_items,
        source_col="referenceSdDocument",
        target_col="deliveryDocument",
        source_type="Order",
        target_type="Delivery",
        relation="order_to_delivery",
    )

    # Delivery -> Invoice via referenceSdDocument
    add_edges_from_relationship(
        billing_document_items,
        source_col="referenceSdDocument",
        target_col="billingDocument",
        source_type="Delivery",
        target_type="Invoice",
        relation="delivery_to_invoice",
    )

    # Invoice -> Payment via invoiceReference
    add_edges_from_relationship(
        payments_accounts_receivable,
        source_col="invoiceReference",
        target_col="accountingDocument",
        source_type="Invoice",
        target_type="Payment",
        relation="invoice_to_payment",
    )

    return G


G = build_sap_otc_graph(
    sales_order_headers,
    outbound_delivery_items,
    billing_document_items,
    payments_accounts_receivable,
)

if __name__ == "__main__":
    print(f"Nodes: {G.number_of_nodes()}")
    print(f"Edges: {G.number_of_edges()}")
