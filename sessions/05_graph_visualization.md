# 05 Graph Visualization

## Initial Prompt
I asked the AI to visualize the graph below each assistant response using the API path.

## AI Response Summary
The first pass used a graph component with node colors and zoom controls. It was enough to prove the concept, but the rendering was a little rough and needed better integration into the existing chat flow.

## Issue Faced
I noticed that the graph could overwhelm the chat if it was too large or too busy. I also had to make sure it rendered only when the API actually returned a path, otherwise the UI felt cluttered.

## Improved Prompt
I refined the request to show the graph inside a card, keep it interactive with zoom and pan, and render it only beneath assistant messages that contained structured path data.

## Final Outcome
The graph view became a useful companion to the JSON output. It helped explain the order-to-cash flow visually without breaking the chat experience, and it fit the rest of the design language better.
