# Strata Legacy GPU

[English](README.md) · [Русский](README.ru.md) · [Windows ZIP](https://github.com/aktalascloud/strata-legacy-gpu/releases/latest)

**Local LLMs on AVX1 CPUs, NVIDIA P40 and AMD Polaris/RX580.** One Windows package, OpenAI-compatible API, independent startup.

| Hardware | Engine | Status |
| --- | --- | --- |
| Ivy Bridge / AVX1, no AVX2 or BMI2 | CPU | Numerical, MTP and API fixture tests |
| Tesla P40 / Pascal sm_61 | CUDA 12.9 | Working native Qwen; embedded CUDA tensor tests |
| Polaris / RX580 8 GB | Vulkan + CPU offload | Experimental binary included; RX580 hardware test pending |

**Models:** Qwen3.8 Flash Next, GLM-5.3-Flash, DeepSeek-V4. MTP requires a matching trained NextN head; missing heads produce an error. V4.1/Engram/DSpark remains a separate source experiment. [Exact support and limits](backends/API-AND-MTP.md).

## Run

1. Download the ZIP, verify `SHA256SUMS.txt`, extract.
2. Run **INSTALL.cmd** and choose native Qwen, CPU, CUDA, Vulkan/RX580 or Poly CUDA. Other models use your local GGUF.
3. Run **START.cmd**. API: `http://127.0.0.1:8093/v1`. For a separate installation, choose a free `--port`; 8080 stays reserved.

**STOP.cmd** drains accepted requests. **CHECK.cmd** verifies files. **AUTOSTART.cmd** registers Windows boot tasks; Codex is not required. Qwen downloads use **resume + SHA-256**; no original checkpoint. No models are included.

## Measured Qwen progress

**16.45 → 48.77 tokens/s** in the engine; whole API: 11.65 → 44.65. Measured 2026-10-25, engine 0.1.49.3, `45B99DC2`. Historical cold response without MTP versus warmed MTP/xhigh: different settings, not a simultaneous A/B. Full 128K and the new models were not benchmarked. [Method and CPU/GPU evidence](p40/BENCHMARKS.md).

Native preset: **128K · KV Q4 · MTP Q2/two drafts · xhigh · CPU vision**. Build: **Ivy Bridge O3/AVX1**, CUDA **O3/sm_61**, MSVC host **O2/Ob3**. Generic profiles start with F16 KV and model-specific limits.

[Patches](p40/PATCHES.md) · [Checks](p40/INSTALLATION-VERIFICATION.md) · [Licenses](THIRD_PARTY_NOTICES.md) · [Upstream Strata](https://github.com/Niko1221/Strata)
[Xolotl](https://github.com/Indras-Mirror/Xolotl) · [PolyStrata](https://github.com/VecSzn/PolyStrata) · [Maya](https://github.com/mw00/project-maya) · [Polaris source](https://github.com/AvilaCarlosDev/polaris-local-ai)

Native engine **0.1.51**, official base [4b9e05a2a806](https://github.com/Niko1221/Strata/commit/4b9e05a2a806a3fe24f7b2560d98626c37dade35). No keys, private settings, logs, caches or SDKs in the ZIP. Trained GLM/DeepSeek and RX580 results are not claimed.
