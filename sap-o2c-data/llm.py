
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


def classify_question(question: str) -> Dict[str, Any]:
    local_intent = _rule_based_intent(question)
    if local_intent.get("query_type") != "unsupported":
        return local_intent

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return _fallback_intent(question)

    client = Groq(api_key=api_key)
    prompt = f"""
You are a classifier for a SAP Order-to-Cash graph query system.

Return only valid JSON with this exact shape:
{{
  "query_type": "trace_order" | "trace_invoice" | "find_orders_without_invoices" | "payment_status" | "full_lifecycle" | "unsupported",
  "entity_id": "string or null"
}}

Rules:
- "trace_order" for order-specific tracing questions such as "show order 740506", "track order", or "order flow".
- "trace_invoice" for invoice-specific tracing questions.
- "find_orders_without_invoices" for questions about missing invoices.
- "payment_status" for questions asking whether an order, invoice, or payment is paid, settled, pending, or open.
- "full_lifecycle" for end-to-end flow questions across the whole order-to-cash lifecycle.
- Use "unsupported" for anything outside the dataset.
- entity_id should be the most relevant numeric id if present, otherwise null.

Question: {question}
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Return only JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        content = response.choices[0].message.content or ""
        data = json.loads(content)
        return _merge_intent(question, data)
    except Exception:
        return _fallback_intent(question)
