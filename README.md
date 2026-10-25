# Strata Legacy GPU

[English](README.md) · [Русский](README.ru.md) · [Download](https://github.com/aktalascloud/strata-legacy-gpu/releases/latest)

**Windows LLM package for AVX1 CPUs, NVIDIA Pascal/P40 and AMD Polaris/RX580.** OpenAI-compatible API; CPU, CUDA and Vulkan backends.

| Hardware | Backend | Validation |
| --- | --- | --- |
| Ivy Bridge / AVX1, no AVX2 | CPU | CPU and API tests |
| NVIDIA Pascal / Tesla P40 | CUDA12.9, sm61 | Working Qwen configuration |
| AMD Polaris / RX5808GB | Vulkan + CPU offload | Backend compiled; RX580 hardware test pending |

**Models:** Qwen3.8 Flash Next, GLM5.3 Flash, DeepSeekV4; V4.1/Engram has a separate DSV41 path. MTP needs a compatible trained head; V4.1 uses DSpark. Model/device limitations: [support guide](backends/API-AND-MTP.md).

## Start

1. Download the Windows ZIP and verify `SHA256SUMS.txt`.
2. Extract; run **INSTALL.cmd**, then **START.cmd**.
3. Open `http://127.0.0.1:8093/`; OpenAI API: `http://127.0.0.1:8093/v1`.

**STOP.cmd** finishes accepted requests. **CHECK.cmd** checks the installation. **AUTOSTART.cmd** registers independent Windows startup; Codex is not required. Weights are separate; downloads use **resume + SHA-256**. No original checkpoint is required.

The currently published binary ZIP is the Qwen/P40 package; the unified CPU/CUDA/Vulkan ZIP is being prepared. Existing weights and settings are retained. Use an unused port; keep OpenWebUI8080 unchanged.

## Measured Qwen result

**16.45 → 48.77 tokens/s** in the engine; whole API: 11.65 → 44.65. Measured 2026-10-25, engine 0.1.49.3, `45B99DC2`. Historical cold response without MTP versus warmed MTP/xhigh: different settings, not a simultaneous A/B. Full 128K and the new models were not benchmarked. [Method and CPU/GPU evidence](p40/BENCHMARKS.md).

Build: **Ivy Bridge O3 / AVX1**, CUDA **O3 / sm61**, MSVC host **O2/Ob3**. Qwen preset: **128K, KV Q4, MTP Q2/two drafts, xhigh, CPU vision**. [Patches](p40/PATCHES.md) · [Checks](p40/INSTALLATION-VERIFICATION.md) · [Licenses](THIRD_PARTY_NOTICES.md).

[Upstream Strata](https://github.com/Niko1221/Strata) · [Xolotl](https://github.com/Indras-Mirror/Xolotl) · [PolyStrata](https://github.com/VecSzn/PolyStrata) · [Maya](https://github.com/mw00/project-maya) · [Polaris source](https://github.com/AvilaCarlosDev/polaris-local-ai).
Engine **0.1.49.3**, official base [7dd5cf18e68c](https://github.com/Niko1221/Strata/commit/7dd5cf18e68c639a8773e096c5c79f971ea2a9f5). No weights, keys, private settings, logs, caches or SDKs in the archive.
