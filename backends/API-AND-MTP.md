# CPU, CUDA and Vulkan models

The Windows ZIP contains the fast native Qwen engine plus embedded CPU/CUDA/Vulkan GGUF workers and Poly CUDA. No separate llama-server, driver or SDK is installed.

| Model | Route | Trained speculation |
| --- | --- | --- |
| DavidAU Qwen3.8 Flash Next | Native P40 preset | Existing Q2 pack, two drafts |
| Qwen35/MoE, Qwen3Next, Qwen4Exp | Embedded CPU/CUDA/Vulkan | Native NextN when complete compatible tensors are present |
| GLM-5.3-Flash (`glm5-next`), GLM DSA (`glm-dsa`) | Embedded CPU/CUDA/Vulkan; Poly CUDA for GLM5Next | Native NextN, model-specific head required |
| DeepSeek-V4 (`deepseek4`) | Embedded CPU/CUDA/Vulkan | Native NextN; no silent fallback |
| DeepSeek-V4.1/Engram | Separate DSV41 source experiment | DSpark; not a qualified binary in this ZIP |

**Quick examples** (use existing local GGUF files):

```bat
INSTALL.cmd --backend vulkan --model "D:\Models\model-00001-of-00002.gguf" --device Vulkan0 --context 32768
INSTALL.cmd --backend cpu --model "D:\Models\model.gguf" --context 32768
INSTALL.cmd --backend cuda --model "D:\Models\model.gguf" --device CUDA0 --draft-model "D:\Models\matching-head.gguf"
```

Choose the first shard; canonical local shards are inspected together without reading tensor payloads. The installer preserves existing installations: extract another folder to prepare another profile. It never downloads weights for a generic backend.

MTP is required by default. `--draft-model` supplies a compatible local GGUF head when absent from the target. `--mtp off` explicitly disables it; lookup guesses, assistants and DSpark are not relabelled as NextN. Qwen4Exp HC tensor shapes and head/target vocabulary are checked. The author's own tokenizer and Jinja are extracted; a Qwen template is never substituted for GLM/DeepSeek.

Use **START.cmd**, **STOP.cmd**, **CHECK.cmd**, **AUTOSTART.cmd**. A local API key is generated for generic profiles in `strata-davidau.json`; keep that file private. Boot/control tasks are independent of Codex. Port8080 is reserved; use a free port for each installation.

The native Qwen preset retains128K/Q4/xhigh/CPU vision. Generic profiles start with F16 KV, a context no larger than model metadata, and1GiB GPU fitting margin. Family-specific vision is not enabled by generic profiles. GLM thinking is on/off; its API does not pretend to implement Qwen's xhigh budget.

**Qualification:** native Qwen passed exact CPU and25 GPU/graph runs. Embedded CPU/CUDA passed synthetic tensor and API/protocol checks; native MTP rejection/partial/full acceptance was tested on an untrained fixture. These are not trained GLM/DeepSeek quality or throughput results. RX580 is absent from the reference host, and its hardware test is pending. Vulkan requires a working Vulkan1.2 driver; optional shader features are detected, not forced. CPU/Vulkan binaries do not import CUDA DLLs.

Source pins, licenses, build-copy compatibility guards and tests are in this directory. The model library is pinned separately from the native Qwen dependency. API changes are integrated into the native aggregate; do not apply an old API overlay again. [Upstream](https://github.com/Niko1221/Strata), [Xolotl](https://github.com/Indras-Mirror/Xolotl), [PolyStrata](https://github.com/VecSzn/PolyStrata), [Maya](https://github.com/mw00/project-maya), [Polaris](https://github.com/AvilaCarlosDev/polaris-local-ai).
