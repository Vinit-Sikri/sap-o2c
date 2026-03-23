# 06 Debugging and Fixes

## Initial Prompt
I asked the AI to help with "the last few issues" after the main features were in place.

## AI Response Summary
The first suggestions were generic: check the API, check the frontend, and ensure the graph path was present. That was directionally right, but not specific enough to fix the actual problems quickly.

## Issue Faced
I ran into CORS behavior from the browser, a build-time dependency gap for the graph library, and a couple of response-shape mismatches when the intent parser changed. I also had to clean up some noisy import behavior in the graph builder.

## Improved Prompt
I got better results when I asked for a targeted debugging pass: verify the exact response contract, keep the frontend logic intact, and fix only the integration points that were breaking the experience.

## Final Outcome
The issues were resolved in smaller steps instead of one big rewrite. That kept the system stable, and it also made the whole project feel easier to maintain because each change was tied to a specific failure I had already observed.
