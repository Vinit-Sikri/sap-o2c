from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from llm import classify_question
from query_engine import (
    find_orders_without_invoices,
    trace_invoice,
    trace_order,
)
from graph_builder import G   # 🔥 IMPORTANT FIX

app = FastAPI(title="SAP Order-to-Cash Query API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str


@app.post("/query")
def query(request: QueryRequest):
    try:
        intent = classify_question(request.question)
        query_type = intent.get("query_type", "unsupported")
        entity_id = intent.get("entity_id")

        if query_type == "unsupported":
            return {
                "question": request.question,
                "query_type": query_type,
                "answer": "This system only answers questions about the dataset.",
            }

        if query_type == "trace_order":
            if not entity_id:
                return {
                    "question": request.question,
                    "query_type": query_type,
                    "answer": "Please provide an order ID.",
                }
            result = trace_order(G, entity_id)   # 🔥 FIX

        elif query_type == "trace_invoice":
            if not entity_id:
                return {
                    "question": request.question,
                    "query_type": query_type,
                    "answer": "Please provide an invoice ID.",
                }
            result = trace_invoice(G, entity_id)   # 🔥 FIX

        elif query_type == "find_orders_without_invoices":
            result = find_orders_without_invoices(G)   # 🔥 FIX

        else:
            return {
                "question": request.question,
                "query_type": "unsupported",
                "answer": "This system only answers questions about the dataset.",
            }

        return {
            "question": request.question,
            "query_type": query_type,
            "result": result,
        }

    except Exception as e:
        return {
            "error": str(e)
        }