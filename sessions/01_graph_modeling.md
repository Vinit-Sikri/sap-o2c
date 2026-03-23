# 01 Graph Modeling

## Initial Prompt
I asked the AI to "build a graph from the SAP Order-to-Cash tables and connect orders, deliveries, invoices, and payments."

## AI Response Summary
The first pass gave me a straightforward NetworkX graph with node types and a few edges. It was useful as a sketch, but it assumed the relationships were already obvious and did not carefully handle missing intermediate records.

## Issue Faced
I noticed the graph was too optimistic. Some deliveries did not have invoices, and some invoices did not have payments yet. My first version also mixed raw IDs across entity types, which made debugging confusing.

## Improved Prompt
I refined the request to: "Build a directed SAP O2C graph with typed nodes for Customer, Order, Delivery, Invoice, and Payment. Prefix node IDs by type, add edges only where relationships exist, and keep the graph tolerant of missing links."

## Final Outcome
The final model was cleaner. I used typed node IDs, added `type` and `entity_id` attributes, and kept the edge logic explicit. That made later traversal and visualization much easier because every node had a stable meaning.
