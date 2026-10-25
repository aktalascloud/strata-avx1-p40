# Current build

Official source `7dd5cf18e68c639a8773e096c5c79f971ea2a9f5`.

- Custom engine0.1.49.3 retains official7dd5cf18e68c and the previous AVX1/P40 optimizations, adding reviewed checkpoint ownership and bounded slot-pressure cache fixes.
- Preserve safe thinking tokens after a budget cut and recognize unambiguous declared namespace-tool names.
- Add compact per-group MMQ scratch with bitwise direct/CUDA Graph tests; keep HC-region reuse disabled.

Measured performance is independently source-pinned in BENCHMARKS.md.
