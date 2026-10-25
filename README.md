# Strata Legacy GPU

[English](README.md) · [Русский](README.ru.md) · [Windows release](https://github.com/aktalascloud/strata-legacy-gpu/releases/latest)

[Strata](https://github.com/Niko1221/Strata) for **AVX1/Ivy Bridge and Tesla P40 (sm_61)**. Verified engine **0.1.49.3**, official base [`7dd5cf18e68c`](https://github.com/Niko1221/Strata/commit/7dd5cf18e68c639a8773e096c5c79f971ea2a9f5). The current ZIP is the qualified **Qwen/P40** package; new adapters are experimental source work.

## Models, backends and MTP

| Model / GPU | Backend | Status |
| --- | --- | --- |
| Qwen3.8 Flash Next / P40 | Strata CUDA + CPU experts | Verified; MTP Q2, two draft tokens |
| GLM 5.3 Flash (`glm5-next`) | Optional Poly CUDA | Experimental; trained NextN head required |
| GLM-DSA, DeepSeek V3/V4 | Embedded GGML CPU / Vulkan | Experimental; MTP needs compatible NextN tensors |
| Polaris / RX580 8 GB | Embedded GGML Vulkan + AVX1 CPU | Experimental; not tested on RX580 hardware |

**MTP needs a compatible trained head.** Strict MTP requests fail when it is unavailable; repetition lookup and external assistants are not called native MTP. The Poly DeepSeek V4 path has no MTP graph; a compatible GGML path is required. No new weights are downloaded for development. RX580 uses Vulkan, not modern HIP; its 8 GB needs model-specific CPU offload.

Sources: [Xolotl](https://github.com/Indras-Mirror/Xolotl), [PolyStrata](https://github.com/VecSzn/PolyStrata), [polaris-local-ai](https://github.com/AvilaCarlosDev/polaris-local-ai) · [Project Maya](https://github.com/mw00/project-maya).

## Qwen / P40 measurements

**16.45 → 48.77 tokens/s** in the engine; whole API: 11.65 → 44.65. Measured 2026-10-25, engine 0.1.49.3, `45B99DC2`. Historical cold response without MTP versus warmed MTP/xhigh: different settings, not a simultaneous A/B. Full 128K and the new models were not benchmarked. [Method and CPU/GPU evidence](p40/BENCHMARKS.md).

## Windows quick start

1. Download ZIP + `SHA256SUMS.txt` from [Releases](https://github.com/aktalascloud/strata-legacy-gpu/releases), verify SHA-256 and extract.
2. Use a Pascal-compatible NVIDIA driver supporting CUDA 12.9. Run **`INSTALL.cmd`**, then **`START.cmd`**. Pinned GGUF/mmproj/MTP use **resume + SHA-256**; no original checkpoint. About **85.6 GB download / 100 GB disk**.
3. Panel: `http://127.0.0.1:8093/`; OpenAI API: `http://127.0.0.1:8093/v1`. **`STOP.cmd`** drains requests; **`CHECK.cmd`** checks without loading weights. **`AUTOSTART.cmd`** registers independent Windows startup/control tasks; Codex is not required.

Preset: **128K / KV q4_0 / author xhigh / MTP Q2 / `--spec 3` / 14 workers / PLE RAM / CPU vision**. Optional `INSTALL.cmd --models-dir D:\Models --port 8094`; choose `--numa-node 0` only after checking topology.

CPU: Clang **O3, `-march=ivybridge -mtune=ivybridge`**, no AVX2/FMA/F16C baseline, strict FP. GPU: **CUDA 12.9, O3, sm_61**; host MSVC `/O2 /Ob3 /favor:INTEL64 /fp:precise`. Applied: AVX1/control/NUMA fixes, Pascal MMQ I64/J96, B6, EXPDEC, IQ staging, QFUSE/GR and checked cache/prefill fixes. [Patches](p40/PATCHES.md) · [Qualification](p40/INSTALLATION-VERIFICATION.md).

MIT and dependency notices: [licenses](THIRD_PARTY_NOTICES.md). VC Runtime comes from Microsoft with signature verification; model licenses apply separately. No weights, keys, private settings, logs, caches or toolchains in the release.
