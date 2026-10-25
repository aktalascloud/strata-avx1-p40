# Optional model backends

Experimental source work; the released and running Qwen/P40 package remains separate.
No model weights are downloaded, no profiles/tasks are activated and no live files are overwritten.

| Engine | Scope | Predictor |
| --- | --- | --- |
| Existing `strata` | Qualified Qwen3.8/P40 + AVX1 experts | Existing Q2 MTP, two drafts |
| `strata-poly` | Experimental GLM5-next/Qwen35 MoE CUDA sm61 + AVX1 experts | Compatible native NextN; other Poly assistants are not called MTP |
| `strata-ggml` | GLM5-next, GLM-DSA, DeepSeek V4, Qwen35 on CPU/CUDA/Vulkan | Compatible native NextN; explicit required/off policy |
| Existing `strata-dsv41` | Separate DeepSeek V4.1/Engram CUDA sm61 build experiment | Trained DSpark blocks; not NextN, pack/model/GPU checks pending |
| RX5808GB | Vulkan + AVX1 CPU, explicit device and memory fitting | Hardware validation pending; no HIP gfx803 bypass |

The separate official model library is pinned to `b9acf138a1e28ce1fc23b5a4fc4b12444b50f7ea`.
The production GGML/Pascal overlay keeps its original pin. Never apply its overlay to the new library mechanically.
`--require-mtp` refuses missing/incompatible canonical heads; it cannot train a head or substitute another model's pack.

[API integration, source builds and local profile preparation](API-AND-MTP.md) · [Source-only fingerprints](source-manifest.json).
CPU fixtures check real native drafts, rejection/partial/full acceptance, seeded sampling, repeated state reset,
and normal/SSE OpenAI requests. These are not learned GLM/DeepSeek, GPU or speed results.
Qwen's existing tokenizer and author effort templates are checked for exact equality; its runtime stays unchanged.

Poly uses current Strata kernels and the pinned Pascal build copy. Missing foreign slot/ID/fused APIs retain
reference fallbacks; no speed gain is claimed. DSV41 compatibility changes only pinned build copies:
const by-value descriptors, unreachable WMMA compile guards and the proper Clang CPU-detection runtime.
All original ISA/SM/SRAM/runtime feature guards are retained. DSV41 stays OFF in production.

Sources: [Strata](https://github.com/Niko1221/Strata), [Xolotl](https://github.com/Indras-Mirror/Xolotl),
[PolyStrata](https://github.com/VecSzn/PolyStrata), [Maya](https://github.com/mw00/project-maya),
[polaris-local-ai](https://github.com/AvilaCarlosDev/polaris-local-ai). Licenses, origins and reviews are retained.
