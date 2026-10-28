# Current build

Official source `5e8a4cca7d690ac60ca37eb09e7d0e010099ad6d`.

- Merge official 0.2.7 / native 0.1.52 with the retained Ivy Bridge/P40 ports and standalone backends.
- QFUSE producer quantization and one-token commit corrections; current native profile passed 26 staged GPU runs plus an exact-library GDN check.
- Updated web chat preserves upstream catalogs/history controls, Russian default and English switch; separate Ultra/Adaptive remain.
- PR4314 rejects boolean/fractional output budgets; guided scheduling retry lost 4.32% and remains OFF.

Measured performance is independently source-pinned in BENCHMARKS.md.
