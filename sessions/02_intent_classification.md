# 02 Intent Classification

## Initial Prompt
I started with a simple request: "Classify user questions into trace order, trace invoice, or missing invoices."

## AI Response Summary
The first classifier worked only for exact phrases like "Trace order 740506." It mapped obvious questions correctly, but it was brittle and missed natural language variations.

## Issue Faced
I tried queries like "Give full journey of order 740506" and "Which orders don't have invoices?" and the classifier failed. It also struggled when the ID was phrased differently or not present at all.

## Improved Prompt
I rewrote the prompt to ask for a hybrid deterministic classifier using keyword rules, regex entity extraction, and synonyms such as trace, track, flow, journey, show, and get. I also asked it to return `unsupported` safely when nothing matched.

## Final Outcome
The classifier became much more robust. It handled flexible phrasing, extracted numeric IDs with regex, and stayed fast because it did not depend on the LLM for every decision. That made the backend feel more production-ready.
