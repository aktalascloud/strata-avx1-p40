# Measured results: Ivy Bridge / Tesla P40

| I | B6 | EXPDEC | Short tok/s | Cached4K tok/s | Harmonic score | vs fresh I64/B0/E0 |
|---|---|---|---|---|---|---|
| 64 | 0 | 0 | 49.0553 | 48.4481 | 48.7498 | +0.000% |
| 64 | 0 | 1 | 49.6316 | 48.3548 | 48.9849 | +0.482% |
| 64 | 1 | 0 | 50.5150 | 48.5584 | 49.5174 | +1.574% |
| 64 | 1 | 1 | 50.2789 | 49.9454 | 50.1116 | +2.793% |
| 64 | 4 | 0 | 50.4732 | 47.9832 | 49.1967 | +0.917% |
| 64 | 4 | 1 | 49.4304 | 48.9821 | 49.2052 | +0.934% |
| 64 | 8 | 0 | 49.2952 | 46.7307 | 47.9787 | -1.582% |
| 64 | 8 | 1 | 47.2534 | 49.7049 | 48.4481 | -0.619% |
| 128 | 0 | 0 | 49.1589 | 44.4877 | 46.7068 | -4.191% |
| 128 | 0 | 1 | 48.7954 | 41.4669 | 44.8336 | -8.033% |
| 128 | 1 | 0 | 49.5011 | 49.3275 | 49.4142 | +1.363% |
| 128 | 1 | 1 | 50.1214 | 45.4352 | 47.6634 | -2.229% |
| 128 | 4 | 0 | 49.3123 | 50.5769 | 49.9366 | +2.434% |
| 128 | 4 | 1 | 48.8624 | 47.6882 | 48.2682 | -0.988% |
| 128 | 8 | 0 | 48.6637 | 46.3600 | 47.4839 | -2.597% |
| 128 | 8 | 1 | 50.3858 | 49.0159 | 49.6914 | +1.931% |

Each arm:2 warmup +5 measured per workload,128 tokens, seed12345/temperature0, author xhigh, cache128/4091. Compilation was stopped during measurement. All rows compare the I/J pair: I64/J96 versus legal I128/J64 (IQ2_S J48). I128/J96 exceeds48KiB and was rejected.

## Worker sweep (same NUMA0 series)

| Workers | Short | Cached4K | Score |
|---|---|---|---|
| 14 | 48.9166 | 50.1194 | 49.5107 |
| 12 | 48.0174 | 49.2062 | 48.6045 |
| 10 | 49.0328 | 48.0102 | 48.5161 |
| 13 | 46.8676 | 49.9707 | 48.3694 |
| 8 | 46.9690 | 48.9222 | 47.9257 |
| 15 | 44.8871 | 46.7324 | 45.7911 |
| 4 | 44.5295 | 44.4336 | 44.4815 |
| 16 | 41.9507 | 41.2238 | 41.5841 |

## IQ/GR combinations, separate sweep

| TABLES/MMVQ/QFUSE/GRfast | Short | Cached4K | Score |
|---|---|---|---|
| 0/0/0/0 | 48.1728 | 47.7808 | 47.9760 |
| 1/0/0/0 | 48.3932 | 49.2402 | 48.8130 |
| 0/1/0/0 | 49.5951 | 47.0329 | 48.2800 |
| 1/1/0/0 | 48.5861 | 48.5290 | 48.5575 |
| 0/0/1/0 | 45.8814 | 47.6013 | 46.7256 |
| 0/0/0/1 | 48.9297 | 48.2910 | 48.6082 |
| 0/0/1/1 | 48.8531 | 49.8054 | 49.3247 |
| 1/1/1/1 | 49.7570 | 51.1080 | 50.4235 |

## Compiler combinations, fresh NUMA profile

| Recipe | Short | Cached4K | Score |
|---|---|---|---|
| O3 | 48.9166 | 50.1194 | 49.5107 |
| ThinLTO | 48.7805 | 50.0098 | 49.3875 |
| Новый PGO | 48.7526 | 50.0020 | 49.3694 |
| Новый PGO+ThinLTO | 47.5660 | 43.6994 | 45.5508 |
| PGO+ThinLTO+CUDA vectorization | 47.8719 | 50.7312 | 49.2601 |
| O3+CUDA vectorization | 48.8047 | 49.4610 | 49.1306 |

## Boundaries

Rates are native decode unless explicitly labelled API total. Thinking tokens count toward generated tokens. The final preset measured50.2789/49.9454 native and47.6324/47.0583 API tokens/s. Fresh4K prefill262.248tokens/s is a separate metric. Full128K throughput was not measured.

The first-install16.4tokens/s used32K/FP16/noMTP/no-thinking/64tokens/temperature1/cold cache. It is historical, not a controlled +205% patch claim. Separate sweeps had separate fresh baselines: never add or multiply their gains. Smaller positive results were retained without an arbitrary cutoff, but are not proof that measurement noise disappeared.

Raw private logs, prompts/responses and host identifiers are deliberately excluded. The public JSON preserves measured rates, method and negative results.
