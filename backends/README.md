# Optional model backends

These sources extend the fork; the released Qwen/P40 runtime remains the production default.
No weights, model downloads, HTTP service, global SDK or driver installation is performed by these targets.

| Engine | Models | Devices | MTP |
| --- | --- | --- | --- |
| Existing `strata` | Qwen3.8 Flash Next | Qualified P40 CUDA + CPU experts | Existing trained Q2 pack |
| `strata-poly` | GLM5-next, Qwen35 MoE, Gemma4, DeepSeek4, LFM2 MoE, Flint | Experimental P40 CUDA + AVX1 experts | GLM/Qwen trained NextN; Gemma uses its separate assistant; other families are not native MTP |
| `strata-ggml` | Architectures implemented by pinned GGML/llama library | CPU or Vulkan, including experimental Polaris | Reviewed native graphs: deepseek2/4, glm-dsa, qwen35/qwen35moe; compatible trained tensors required |

`--require-mtp` never falls back silently. It cannot create a prediction head absent from a model.
The native Qwen3.8 MTP pack is not interchangeable with a GGUF NextN head or a GLM head.
Model compatibility still needs real-model validation; RX580 has not been hardware-qualified here.

## Source builds

The GGML adapter is embedded: no separate llama-server runtime is built or installed.
Its exact dependency is Strata's existing `3cf03257f219afbe7334045ff7c6a06ac68c627d`.

```sh
cmake -S backends/ggml -B build-ggml -DSTRATA_LLAMA_SOURCE=/path/to/pinned/llama.cpp -DSTRATA_DEVICE=vulkan -DGGML_CCACHE=OFF
cmake --build build-ggml --target strata-ggml --parallel 12
```

Use an AVX1-safe compiler profile: O3, Ivy Bridge, no AVX2/FMA/F16C baseline and no fast-math.
Vulkan needs a local SDK with `glslc` and SPIRV-Headers; neither a driver nor a global SDK is installed by this build.
Device feature detection retains the F32 fallback; do not force FP16, integer-dot or cooperative-matrix features on Polaris.

Poly targets are injected after the reviewed core's CMake configuration through `inject.cmake`.
They use CUDA12.9/sm61, the existing Pascal build copy and current Strata kernels.
Optional foreign slot/ID kernels currently take their documented per-matrix fallback; the missing fused RMS operation takes its separate reference operations.
Those fallbacks have no claimed speed gain. GDN tensor-core prefill is not enabled on Pascal.

Example engine arguments for a future compatible GLM file: `--model MODEL.gguf --serve --require-mtp --window 3 --lookup 0 --kv-whole --any-node --threads 14`.
Check `--help`: these options differ from Qwen's `--spec 3`; KV q4_0 is not a universal Poly format.
Do not substitute this example into an active production profile without complete API/tokenizer/parser and model qualification.

## Provenance

[Xolotl](https://github.com/Indras-Mirror/Xolotl), [PolyStrata](https://github.com/VecSzn/PolyStrata),
[polaris-local-ai](https://github.com/AvilaCarlosDev/polaris-local-ai), [Project Maya](https://github.com/mw00/project-maya).
Poly's exact origin, MIT license, compatibility diff and pre-build review are retained in `poly/`.
Maya's Pascal/AVX guards, MTP state handling and issues are reviewed separately; its speed reports are not measurements of this fork.
