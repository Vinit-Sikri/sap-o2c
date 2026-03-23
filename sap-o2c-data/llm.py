
import json
import os
import re
from typing import Any, Dict, Optional

from groq import Groq


SUPPORTED_QUERIES = {
    "trace_order",
    "trace_invoice",
    "find_orders_without_invoices",
    "payment_status",
    "full_lifecycle",
    "unsupported",
}


ENTITY_PATTERNS = {
    "order": re.compile(r"\border\s*(?:id\s*)?[:#-]?\s*(\d{4,})\b", re.IGNORECASE),
    "invoice": re.compile(r"\binvoice\s*(?:id\s*)?[:#-]?\s*(\d{4,})\b", re.IGNORECASE),
    "payment": re.compile(r"\bpayment\s*(?:id\s*)?[:#-]?\s*(\d{4,})\b", re.IGNORECASE),
    "delivery": re.compile(r"\bdelivery\s*(?:id\s*)?[:#-]?\s*(\d{4,})\b", re.IGNORECASE),
}


def _clean_text(question: str) -> str:
    return re.sub(r"\s+", " ", question.strip().lower())


def _first_numeric_id(question: str) -> Optional[str]:
    matches = re.findall(r"\b\d{4,}\b", question)
    return matches[0] if matches else None


def _extract_entity_id(question: str, query_type: str) -> Optional[str]:
    text = question.strip()

    if query_type == "trace_invoice":
        for key in ("invoice", "payment", "delivery"):
            match = ENTITY_PATTERNS[key].search(text)
            if match:
                return match.group(1)

    if query_type in {"trace_order", "payment_status", "full_lifecycle"}:
        for key in ("order", "invoice", "payment", "delivery"):
            match = ENTITY_PATTERNS[key].search(text)
            if match:
                return match.group(1)

    return _first_numeric_id(text)


def _normalize_query_type(query_type: Any) -> str:
    if not isinstance(query_type, str):
        return "unsupported"
    value = query_type.strip().lower()
    if value in SUPPORTED_QUERIES:
        return value
    aliases = {
        "order_flow": "trace_order",
        "track_order": "trace_order",
        "show_order": "trace_order",
        "invoice_flow": "trace_invoice",
        "track_invoice": "trace_invoice",
        "show_invoice": "trace_invoice",
        "missing_invoices": "find_orders_without_invoices",
    }
    return aliases.get(value, "unsupported")


def _rule_based_intent(question: str) -> Dict[str, Any]:
    text = _clean_text(question)
    entity_id = None

    if not text:
        return {"query_type": "unsupported"}

    if any(phrase in text for phrase in ("without invoice", "without invoices", "missing invoice", "missing invoices")):
        return {"query_type": "find_orders_without_invoices"}

    if any(phrase in text for phrase in ("payment status", "payment state", "paid status", "invoice paid", "has payment")):
        entity_id = _extract_entity_id(question, "payment_status")
        return {"query_type": "payment_status", "entity_id": entity_id}

    if any(phrase in text for phrase in ("full lifecycle", "full flow", "end to end", "end-to-end", "complete flow")):
        entity_id = _extract_entity_id(question, "full_lifecycle")
        return {"query_type": "full_lifecycle", "entity_id": entity_id}

    if any(phrase in text for phrase in ("trace order", "show order", "track order", "order flow", "order status", "order lifecycle")):
        entity_id = _extract_entity_id(question, "trace_order")
        return {"query_type": "trace_order", "entity_id": entity_id}

    if any(phrase in text for phrase in ("trace invoice", "show invoice", "track invoice", "invoice flow")):
        entity_id = _extract_entity_id(question, "trace_invoice")
        return {"query_type": "trace_invoice", "entity_id": entity_id}

    if "order" in text and ("flow" in text or "track" in text or "show" in text):
        entity_id = _extract_entity_id(question, "trace_order")
        return {"query_type": "trace_order", "entity_id": entity_id}

    if "invoice" in text and ("flow" in text or "track" in text or "show" in text):
        entity_id = _extract_entity_id(question, "trace_invoice")
        return {"query_type": "trace_invoice", "entity_id": entity_id}

    return {"query_type": "unsupported"}


def _fallback_intent(question: str) -> Dict[str, Any]:
    intent = _rule_based_intent(question)
    query_type = intent.get("query_type", "unsupported")
    if query_type == "unsupported":
        return {"query_type": "unsupported"}
    return {
        "query_type": query_type,
        "entity_id": intent.get("entity_id"),
    }


def _merge_intent(question: str, data: Dict[str, Any]) -> Dict[str, Any]:
    query_type = _normalize_query_type(data.get("query_type"))
    if query_type == "unsupported":
        return _fallback_intent(question)

    entity_id = data.get("entity_id")
    if not entity_id and query_type != "find_orders_without_invoices":
        entity_id = _extract_entity_id(question, query_type)

    result = {"query_type": query_type}
    if entity_id is not None:
        result["entity_id"] = str(entity_id)
    return result


def classify_question(question: str) -> dict:
    import re

    # Normalize once so matching is case-insensitive and resilient to extra spacing.
    text = re.sub(r"\s+", " ", (question or "").strip().lower())

    if not text:
        return {"query_type": "unsupported"}

    # Fast regex for numeric identifiers. This keeps entity extraction deterministic
    # and avoids depending on brittle exact phrases.
    id_match = re.search(r"\b\d{4,}\b", text)
    entity_id = id_match.group(0) if id_match else None

    # Synonyms for intent detection.
    # These rules exist to make the classifier robust to natural language variation
    # without requiring exact prompt wording.
    trace_words = r"(trace|track|follow|show|get|give|view|display|see|fetch)"
    journey_words = r"(journey|flow|path|route|lifecycle|journey)"
    invoice_words = r"(invoice|billing|bill)"
    order_words = r"(order|orders|sales order|salesorder)"
    invoice_missing_words = r"(don't have invoices|dont have invoices|without invoices|missing invoices|no invoices|lacking invoices|have no invoices)"
    invoice_present_words = r"(with invoices|have invoices|has invoices|invoiced orders)"
    payment_words = r"(payment|paid|settled|collection|cash)"

    # 1) Missing-invoice detection must win early.
    # This prevents questions like "Which orders don't have invoices?" from being
    # misclassified as trace_order just because they mention "orders".
    if re.search(order_words, text) and re.search(invoice_missing_words, text):
        return {"query_type": "find_orders_without_invoices"}

    # 2) Orders with invoices.
    # Useful for analytics-style questions about orders that already reached billing.
    if re.search(order_words, text) and re.search(invoice_present_words, text):
        return {"query_type": "find_orders_with_invoices"}

    # 3) Invoice tracing.
    # We look for invoice/billing wording plus a flow/journey/trace verb.
    # This makes "Show me invoice flow" and "Track invoice 900540298" both work.
    if re.search(invoice_words, text) and (
        re.search(trace_words, text) or re.search(journey_words, text) or "flow" in text
    ):
        return {
            "query_type": "trace_invoice",
            "entity_id": entity_id,
        }

    # 4) Order tracing.
    # We support flexible phrasing like:
    # - "Give full journey of order 740506"
    # - "Track this order"
    # - "order flow"
    # - "get order status"
    if re.search(order_words, text) and (
        re.search(trace_words, text) or re.search(journey_words, text) or "flow" in text or "status" in text
    ):
        return {
            "query_type": "trace_order",
            "entity_id": entity_id,
        }

    # 5) Payment status queries.
    # Kept separate because they often sound like "payment status" rather than tracing.
    if re.search(payment_words, text) and "status" in text:
        return {
            "query_type": "payment_status",
            "entity_id": entity_id,
        }

    # 6) Flexible fallback for short queries.
    # If the user says "track order" or "show invoice flow" without a numeric ID,
    # we still return the intent with entity_id=None so the caller can prompt for it.
    if re.search(order_words, text) and ("track" in text or "trace" in text or "flow" in text or "journey" in text):
        return {"query_type": "trace_order", "entity_id": entity_id}

    if re.search(invoice_words, text) and ("track" in text or "trace" in text or "flow" in text or "journey" in text):
        return {"query_type": "trace_invoice", "entity_id": entity_id}

    return {"query_type": "unsupported"}
