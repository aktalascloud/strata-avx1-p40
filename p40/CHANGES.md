# Current build

Official source `4b9e05a2a806a3fe24f7b2560d98626c37dade35`.

- Native0.1.51: empty OpenAI message arrays return400; one-token probes no longer report an absurd decode rate.
- Local PR2638: AVX1 IQ4_NL down dispatch correction, two-row NT1, exact FP16 fast conversion and reused Q2_0 activation sums; CPU/numerical gates passed, no throughput claim.
- Universal package retains the same checked CPU/CUDA/Vulkan/Poly component bytes; their actual prior build versions and experimental RX580/trained-model limits are preserved.

Measured performance is independently source-pinned in BENCHMARKS.md.
