# Original installation and latest selected result

| Generation | First installation | Latest selected result |
|---|---|---|
| Engine tokens/s | 16.40 | 47.66 |
| Whole-request API tokens/s | 11.65 | 42.71 |

Latest measurement: **2026-10-24**, engine **0.1.49.2**, source `7dd5cf18e68c`. Cached 4K engine decode: 46.11 tokens/s.

First installation: one cold response of 64 tokens, 32K/FP16, no MTP or reasoning. Latest: median of five warmed responses of 128 tokens after two warmups; 128K/Q4, MTP Q2, xhigh, temperature 0, seed 12345. Settings differ: overall progress is not an isolated patch gain. Full 128K throughput was not measured.

Separate controlled whole-model experiments support CPU tuning (14 workers: +3.307%; NUMA 0: +1.454%) and GPU tuning (IQ/QFUSE/GR: +5.101%; B6/EXPDEC: +2.793%). Those effects were measured on `011c9e6`; never add them. Intermediate releases and sweep tables are omitted.

Hardware: 2 x Xeon E5-2697 v2, 16 visible threads, 256 GiB RAM, Tesla P40 24 GiB, Windows. Rate = 1000 * predicted_n / predicted_ms. Thinking tokens count. No frontend benchmark.

[Structured evidence](results/benchmarks.json). No private payloads, responses, host identifiers or raw logs.
