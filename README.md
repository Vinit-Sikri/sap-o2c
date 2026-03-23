# 🔗 SAP O2C Context Graph — LLM-Powered Business Intelligence System

> **Live Demo:** [https://sap-o2c-r295.onrender.com](https://sap-o2c-r295.onrender.com)

A **context graph system with a conversational query interface** built on real SAP Order-to-Cash (O2C) business data. Fragmented transactional records across orders, deliveries, invoices, and payments are unified into an interactive knowledge graph — queryable entirely through natural language.

---

## 📌 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Database & Graph Design](#database--graph-design)
- [LLM Prompting Strategy](#llm-prompting-strategy)
- [Guardrails](#guardrails)
- [Graph Visualization](#graph-visualization)
- [Example Queries](#example-queries)
- [Project Structure](#project-structure)
- [Running Locally](#running-locally)
- [Key Design Decisions](#key-design-decisions)

---

## Overview

Real-world SAP business data is spread across disconnected tables — sales orders, deliveries, billing documents, payments, customers, products, and more. There is no single view that shows how a transaction flows end-to-end.

This project solves that by:

1. **Ingesting** the dataset and constructing a typed, directed graph of business entities
2. **Visualizing** the graph interactively so users can explore nodes, relationships, and metadata
3. **Exposing a chat interface** where users ask questions in plain English
4. **Dynamically generating SQL-like queries** from those questions using an LLM
5. **Executing those queries** against the underlying data and returning grounded, accurate answers

The system is **not** a static FAQ or hardcoded Q&A pipeline. Every answer is derived from live data at query time.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                        │
│                                                                 │
│   ┌─────────────────────────┐   ┌──────────────────────────┐   │
│   │   Graph Visualizer      │   │   Chat Interface          │   │
│   │   (React Flow)          │   │   (Natural Language)      │   │
│   │                         │   │                           │   │
│   │  • Expandable nodes     │   │  • User types question    │   │
│   │  • Node metadata panel  │   │  • Streams LLM response   │   │
│   │  • Typed edges          │   │  • Grounded in data       │   │
│   └────────────┬────────────┘   └────────────┬─────────────┘   │
│                │                              │                  │
└────────────────┼──────────────────────────────┼──────────────────┘
                 │        REST API (FastAPI)     │
┌────────────────┼──────────────────────────────┼──────────────────┐
│                ▼                              ▼                  │
│   ┌─────────────────────┐    ┌──────────────────────────────┐   │
│   │   Graph Endpoints   │    │   Query Endpoint              │   │
│   │   /api/graph/*      │    │   /api/chat                   │   │
│   └──────────┬──────────┘    └──────────────┬───────────────┘   │
│              │                               │                   │
│   ┌──────────▼──────────┐    ┌──────────────▼───────────────┐   │
│   │   NetworkX Graph    │    │   LLM Orchestration Layer    │   │
│   │   (In-Memory)       │    │   (Groq — llama3-70b)        │   │
│   │                     │    │                               │   │
│   │  Nodes: Orders,     │    │  1. Intent classification    │   │
│   │  Deliveries,        │    │  2. Schema injection          │   │
│   │  Invoices,          │    │  3. SQL/query generation      │   │
│   │  Payments,          │    │  4. Query execution           │   │
│   │  Customers,         │    │  5. Answer synthesis          │   │
│   │  Products,          │    │                               │   │
│   │  Addresses          │    └──────────────┬───────────────┘   │
│   └──────────┬──────────┘                   │                   │
│              │                               │                   │
│   ┌──────────▼───────────────────────────────▼───────────────┐  │
│   │                  Pandas DataFrames                        │  │
│   │          (Loaded from CSV dataset at startup)             │  │
│   └───────────────────────────────────────────────────────────┘  │
│                          BACKEND (FastAPI)                       │
└──────────────────────────────────────────────────────────────────┘
```

### Data Flow for a Chat Query

```
User Question
     │
     ▼
[Guardrail Check] ──── Off-topic? ──▶ Reject with standard message
     │
     ▼ (On-topic)
[Schema Context Injection]
     │  Inject: table names, column names, sample rows, entity relationships
     ▼
[Groq LLM — Query Generation]
     │  Output: Python/pandas expression or SQL-style logic
     ▼
[Query Execution] ──── Error? ──▶ Retry with error feedback
     │
     ▼
[Groq LLM — Answer Synthesis]
     │  Ground the answer in returned data rows
     ▼
Natural Language Response → User
```

---

## Tech Stack

| Layer | Technology | Reason |
|---|---|---|
| **Backend API** | Python + FastAPI | Async support, fast, Pythonic — ideal for data-heavy pipelines |
| **Graph Engine** | NetworkX | Pure Python, flexible typed graph construction without a DB dependency |
| **Data Layer** | Pandas DataFrames | Efficient in-memory tabular operations for query execution |
| **LLM Provider** | Groq (llama3-70b-8192) | Free tier, extremely low latency, strong reasoning on structured data |
| **Frontend** | React (Vite) | Component-based, fast dev experience |
| **Graph Visualization** | React Flow | Production-grade graph rendering with custom node/edge support |
| **Deployment** | Render.com | Zero-config deploys, free tier with persistent services |

---

## Database & Graph Design

### Why In-Memory (NetworkX + Pandas)?

This project deliberately avoids a persistent database. Here's the reasoning:

- **Dataset size**: The SAP O2C dataset fits entirely in memory. There is no query latency benefit from a disk-based DB.
- **Graph flexibility**: NetworkX allows arbitrary node attributes and edge types without schema migrations. This made rapid iteration possible.
- **LLM query execution**: The LLM generates Pandas expressions — this is simpler, safer, and faster than generating SQL for a live relational DB.
- **Deployment simplicity**: No external DB service required. The app loads the dataset at startup and serves all requests from memory.

> For a production system handling millions of records, this would be replaced by PostgreSQL + pgvector (relational queries + semantic search) and Neo4j (deep graph traversal). At this scale, NetworkX + Pandas is the right pragmatic choice.

### Graph Schema

**Node Types**

| Node Type | Key Attributes |
|---|---|
| `SalesOrder` | order_id, customer_id, order_date, status, net_value |
| `SalesOrderItem` | item_id, order_id, material_id, quantity, price |
| `Delivery` | delivery_id, order_id, delivery_date, plant, status |
| `BillingDocument` | billing_id, delivery_id, billing_date, amount |
| `JournalEntry` | entry_id, billing_id, amount, posting_date |
| `Customer` | customer_id, name, region, address_id |
| `Material` | material_id, description, category |
| `Address` | address_id, city, country, postal_code |

**Edge Types (Relationships)**

```
SalesOrder      ──[HAS_ITEM]──▶         SalesOrderItem
SalesOrder      ──[PLACED_BY]──▶        Customer
SalesOrder      ──[FULFILLED_BY]──▶     Delivery
SalesOrderItem  ──[REFERENCES]──▶       Material
Delivery        ──[SHIPS_TO]──▶         Address
Delivery        ──[BILLED_AS]──▶        BillingDocument
BillingDocument ──[RECORDED_IN]──▶      JournalEntry
Customer        ──[LOCATED_AT]──▶       Address
```

This schema captures the **complete O2C flow**: a customer places a sales order → items are fulfilled via delivery → delivery generates a billing document → billing is recorded as a journal entry.

---

## LLM Prompting Strategy

The LLM is used in two distinct steps for every chat query.

### Step 1 — Query Generation Prompt

The system prompt injects the full data schema before asking the LLM to generate a query:

```
You are a data analyst working with SAP Order-to-Cash business data.

You have access to the following Pandas DataFrames:
- df_orders: columns [order_id, customer_id, order_date, status, net_value, ...]
- df_items: columns [item_id, order_id, material_id, quantity, net_price, ...]
- df_deliveries: columns [delivery_id, order_id, delivery_date, plant, status, ...]
- df_billing: columns [billing_id, delivery_id, billing_date, amount, ...]
- df_journal: columns [entry_id, billing_id, amount, posting_date, ...]
- df_customers: columns [customer_id, name, region, city, ...]
- df_materials: columns [material_id, description, category, ...]

User Question: {user_question}

Generate a single Python expression using these DataFrames that answers the question.
Return ONLY the Python/pandas code. No explanation. No markdown.
```

**Key decisions:**
- **Schema injection over fine-tuning**: Injecting column names and sample rows at runtime is more reliable than relying on the model's prior knowledge of SAP data structures.
- **Code generation over SQL**: Pandas code is easier to validate, sandbox, and debug than raw SQL strings.
- **One expression constraint**: Forcing a single expression prevents multi-step code that is harder to safely execute.

### Step 2 — Answer Synthesis Prompt

After the query executes and returns a result, a second call synthesizes the final answer:

```
You are a business intelligence assistant. A user asked:
"{user_question}"

A query was executed and returned this result:
{query_result}

Write a clear, concise answer in 1-3 sentences grounded strictly in this data.
Do not add information not present in the result. Do not speculate.
```

**Key decisions:**
- **Two-step separation**: Separating query generation from answer synthesis prevents hallucination. The model synthesizing the answer only sees real data rows, never the raw data tables.
- **Strict grounding instruction**: Explicitly telling the model not to add information outside the result is critical for factual accuracy.
- **Short answer constraint**: Business users want concise answers, not essays.

### Model Choice: `llama3-70b-8192` via Groq

- **Speed**: Groq's LPU inference delivers sub-second latency, making the chat feel responsive.
- **Reasoning quality**: llama3-70b reliably generates valid Pandas code for moderately complex joins and aggregations.
- **Free tier**: 30 RPM / 14,400 RPD — sufficient for a demo system.

---

## Guardrails

Guardrails prevent the system from being misused as a general-purpose chatbot.

### Implementation: Two-Layer Defense

**Layer 1 — Intent Classifier (LLM-based)**

Before any query is processed, a lightweight classification call determines if the question is relevant to the dataset:

```
You are a classifier. Determine if the following question is related to 
SAP Order-to-Cash business data (orders, deliveries, billing, payments, 
customers, products, logistics).

Question: "{user_question}"

Reply with only one word: RELEVANT or IRRELEVANT
```

If the response is `IRRELEVANT`, the system immediately returns:

```
This system is designed to answer questions related to the 
SAP Order-to-Cash dataset only. Please ask questions about 
orders, deliveries, billing documents, customers, or products.
```

**Layer 2 — Execution Sandbox**

Even if a query passes the classifier, the generated Pandas code is executed inside a restricted namespace:

```python
# Only these names are available during exec()
safe_namespace = {
    "df_orders": df_orders,
    "df_items": df_items,
    "df_deliveries": df_deliveries,
    "df_billing": df_billing,
    "df_journal": df_journal,
    "df_customers": df_customers,
    "df_materials": df_materials,
    "pd": pd,
}
```

- No access to `os`, `sys`, `open`, `exec`, `eval`, or any system-level module
- Any `NameError` or `AttributeError` is caught and returns a safe error message
- No code is persisted or written to disk

**Rejected query examples:**

| Input | Response |
|---|---|
| `"Write a poem about logistics"` | Standard domain rejection message |
| `"What is the capital of France?"` | Standard domain rejection message |
| `"List all Python builtins"` | Caught by execution sandbox |
| `"Who won the cricket match?"` | Standard domain rejection message |

---

## Graph Visualization

Built with **React Flow** — a production-grade React library for node-based interfaces.

### Features

- **Expandable nodes**: Click any node to expand its connected neighbors
- **Node type coloring**: Each entity type (Order, Delivery, Billing, Customer, etc.) has a distinct color
- **Metadata panel**: Clicking a node opens a side panel showing all attributes
- **Relationship labels**: Edges are labeled with the relationship type (`HAS_ITEM`, `BILLED_AS`, etc.)
- **Minimap**: Bottom-right minimap for navigating large subgraphs
- **Zoom & pan**: Standard React Flow controls

### Design Decision: On-Demand Expansion

Rather than rendering the entire graph at once (which would be unreadable with hundreds of nodes), the UI loads a **seed set of nodes** and expands on click. This keeps the visualization usable and performant.

---

## Example Queries

These queries are supported out of the box:

```
Which products are associated with the highest number of billing documents?

Trace the full flow of billing document [ID] from sales order to journal entry.

Which sales orders have been delivered but not yet billed?

Which customers have the highest total order value?

Show all deliveries to a specific plant.

Which billing documents have no corresponding journal entry?

What is the average delivery time between order date and delivery date?

List all incomplete O2C flows — orders missing delivery, billing, or payment.
```

---

## Project Structure

```
sap-o2c/
├── backend/
│   ├── main.py                  # FastAPI app, routes
│   ├── graph_builder.py         # NetworkX graph construction
│   ├── query_engine.py          # LLM orchestration, query execution
│   ├── guardrails.py            # Intent classification, sandbox
│   ├── data_loader.py           # CSV ingestion, Pandas DataFrames
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── GraphViewer.jsx  # React Flow graph component
│   │   │   ├── ChatPanel.jsx    # Conversational interface
│   │   │   ├── NodeDetail.jsx   # Node metadata side panel
│   │   │   └── Layout.jsx       # App shell
│   │   ├── hooks/
│   │   │   └── useGraph.js      # Graph state management
│   │   ├── api/
│   │   │   └── client.js        # FastAPI client
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
│
├── data/
│   └── *.csv                    # SAP O2C dataset
│
└── README.md
```

---

## Running Locally

### Prerequisites

- Python 3.10+
- Node.js 18+
- Groq API key (free at [console.groq.com](https://console.groq.com))

### Backend

```bash
cd backend
pip install -r requirements.txt

# Set your Groq API key
export GROQ_API_KEY=your_key_here

uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install

# Point to local backend
echo "VITE_API_URL=http://localhost:8000" > .env

npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

---

## Key Design Decisions

### Why not Neo4j?

Neo4j would be the natural choice for a graph database. It was deliberately not used here because:

1. The dataset fits in memory — a full graph DB adds operational overhead with no query performance benefit at this scale
2. LLM-generated Cypher (Neo4j's query language) is less reliable than Pandas code for smaller models
3. NetworkX + Pandas is zero-infrastructure and deploys as part of the Python process itself

For a production system with millions of nodes and deep graph traversal queries (e.g., 6-hop relationship paths), Neo4j would be the right call.

### Why Groq over OpenAI/Gemini?

- **Latency**: Groq's hardware delivers ~10x lower latency than OpenAI API at equivalent model quality
- **Free tier generosity**: 14,400 requests/day — enough for continuous demo usage
- **llama3-70b quality**: Sufficient for structured data query generation without GPT-4 costs

### Why Two LLM Calls per Query?

A single call that both generates the query AND writes the final answer risks hallucinating details not present in the data. Separating the steps ensures:

- **Call 1**: Model sees schema + question → produces executable code only
- **Call 2**: Model sees only the actual query result → synthesizes a grounded answer

This separation is the most important architectural guardrail in the system.

### Why React Flow over D3?

D3 gives maximum flexibility but requires significant custom code for interactive graph UIs. React Flow provides:
- Built-in node drag, zoom, pan
- Custom node/edge render components in React JSX
- Minimap, controls, and background out of the box
- A significantly faster development path for a polished result

---

## Live Demo

🌐 **[https://sap-o2c-r295.onrender.com](https://sap-o2c-r295.onrender.com)**

> Note: The app is hosted on Render's free tier. It may take 30–60 seconds to wake from sleep on first load.

---

## Author
Vinit Sikri
Built as part of a take-home assignment evaluating system design, AI-assisted development, and pragmatic engineering decisions.

> *"We're evaluating your architectural decisions, your reasoning, and how effectively you use AI to arrive at them."*
