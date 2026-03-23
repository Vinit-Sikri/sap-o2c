# 03 Backend API

## Initial Prompt
I asked the AI to create a FastAPI `/query` endpoint that would call the graph logic and return results for the frontend.

## AI Response Summary
The first version was functional, but it was too bare. It returned raw structured data without much user-friendly context, and the response handling was not very defensive.

## Issue Faced
I ran into a few practical issues. CORS needed to be enabled for the React app, the graph object had to be imported consistently, and the API responses needed to stay structured while also being readable.

## Improved Prompt
I tightened the prompt to keep the same JSON shape but add assistant-like fields such as `summary`, `status`, and `insight`. I also asked for guardrails so unsupported questions would get a safe fallback message instead of hallucinated output.

## Final Outcome
The API became much easier to use from the frontend. It still returned machine-readable graph data, but now the response felt like an AI assistant and handled unsupported queries gracefully.
