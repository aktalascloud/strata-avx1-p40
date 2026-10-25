# Current build

Official source `41cf05a06a25dd29103b7b27a2279a3f60c21876`.

- Upstream native0.1.50: asynchronous-tier auto selection when unset and guarded AVX512 self-checks; explicit async1 and the Ivy/P40 profile are preserved.
- Local universal Windows kit: native Qwen, embedded CPU/CUDA/Vulkan and Poly CUDA, local GGUF/shard selection, compatible NextN checks and OpenAI API. RX580 remains experimental.
- Local compatibility/security: BMI2 disabled for Ivy Bridge, bounded grammar/JSON recursion and Vulkan large-view handling. Native25 numerical/graph runs including5201 DenseF32 passed; no new throughput benchmark.

Measured performance is independently source-pinned in BENCHMARKS.md.
