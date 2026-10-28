# Original installation and latest selected result

| Generation | First installation | Latest measurement |
|---|---|---|
| Engine tokens/s | 16.45 | 44.45 |
| Whole-request API tokens/s | 11.65 | 40.35 |

Latest measurement: **2026-10-28**, engine **0.1.52**, binary `E1D5A2FB`, source `5e8a4cca7d69`. Cached 4K: **44.46** engine tokens/s and **39.56** whole-request API tokens/s.

First installation: preserved historical cold 64-token measurement, 32K/FP16, no MTP or reasoning; the stock binary was not rerun. Latest: median of 3 warmed 128-token responses after 2 warmups; 128K/Q4, MTP Q2, Ultra/xhigh, temperature 0, seed 12345. Settings differ: this is historical progress, not a simultaneous binary A/B or an isolated patch gain. Full 128K throughput was not measured.

Separate controlled whole-model experiments support CPU tuning (14 workers: +3.307%; NUMA 0: +1.454%) and GPU tuning (IQ/QFUSE/GR: +5.101%; B6/EXPDEC: +2.793%). Those effects were measured on `011c9e6`; never add them. Intermediate releases and sweep tables are omitted.

The guided CPU scheduling retry on this engine measured -4.32% by the harmonic mean of two workloads; it remains OFF. CPU-only micro results are not whole-model gains.

Hardware: 2 x Xeon E5-2697 v2, 16 visible threads, 256 GiB RAM, Tesla P40 24 GiB, Windows. Rate = 1000 * predicted_n / predicted_ms. Thinking tokens count. No frontend benchmark.

[Structured evidence](results/benchmarks.json). No private payloads, responses, host identifiers or raw logs.
