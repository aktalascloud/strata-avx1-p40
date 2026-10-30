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

**RU/EN interface · separate Ultra and Adaptive modes.** Adaptive/Auto is the default. Explicit High/XHigh retain stock Qwen semantics. Adaptive selects an author persona per task; no memory service or database is included. [Modes and API](p40/REASONING-MODES.md) · [Mnemosyne source](https://github.com/TheHubUser4860938/Strata-Mnemosyne).

**16.45 → 55.15 tokens/s** in the engine; whole API: 11.65 → 48.92. Measured 2026-10-29, engine 0.1.53, `C0736323`. Historical cold response without MTP versus warmed MTP/Ultra: different settings, not a simultaneous A/B. Full 128K and the new models were not benchmarked. [Method and CPU/GPU evidence](p40/BENCHMARKS.md).

Native preset: **128K · KV Q4 · MTP Q2/two drafts · xhigh · CPU vision**. Build: **Ivy Bridge O3/AVX1**, CUDA **O3/sm_61**, MSVC host **O2/Ob3**. Generic profiles start with F16 KV and model-specific limits.

Measured P40 setting: `STRATA_Q8_SM60=1`, `STRATA_MTP_Q8_SM60=0`; the latter leaves MTP Q2 enabled. Other GPUs were not timed for this choice.

[Patches](p40/PATCHES.md) · [Checks](p40/INSTALLATION-VERIFICATION.md) · [Licenses](THIRD_PARTY_NOTICES.md) · [Upstream Strata](https://github.com/Niko1221/Strata)
[Xolotl](https://github.com/Indras-Mirror/Xolotl) · [PolyStrata](https://github.com/VecSzn/PolyStrata) · [Maya](https://github.com/mw00/project-maya) · [Polaris source](https://github.com/AvilaCarlosDev/polaris-local-ai)

Native engine **0.1.54**, official base [870aedd9e1eb](https://github.com/Niko1221/Strata/commit/870aedd9e1ebe1c91f94da93b59af17729f6c5c0). No keys, private settings, logs, caches or SDKs in the ZIP. Trained GLM/DeepSeek and RX580 results are not claimed.
