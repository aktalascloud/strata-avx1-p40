# Current build

Official source `4b9e05a2a806a3fe24f7b2560d98626c37dade35`.

- Separate Ultra and Adaptive author modes; explicit High/XHigh retain stock Qwen behavior.
- Russian interface with English switch; user/model text and code remain unchanged.
- Stateless routing adapted from MIT Strata-Mnemosyne; no memory, database or embedding service.
- Native/vision/CUDA bytes unchanged; existing 25 numerical/graph checks retained, with separate serving/API/UI checks.

Measured performance is independently source-pinned in BENCHMARKS.md.
