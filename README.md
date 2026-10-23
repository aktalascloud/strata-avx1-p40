# Strata for AVX1 and Tesla P40

[English](README.md) | [Русский](README.ru.md)

A community fork of [Strata](https://github.com/Niko1221/Strata), tested on Ivy Bridge Xeons without AVX2 and an NVIDIA Tesla P40. It includes reviewed patches, measured tuning results, and a portable Windows package.

The reference model is **DavidAU Qwen3.8-Flash-Next IQ3_S**, with MTP Q2 and a CPU vision projector.

**Reference performance: 50.28 and 49.95 tokens/s in the engine, or 47.63 and 47.06 tokens/s including API overhead.** These are warmed short-prompt and cached 4K-context measurements, not a guarantee for every workload.

The packaged engine is **0.1.47**, based on upstream commit [`011c9e600a93`](https://github.com/Niko1221/Strata/commit/011c9e600a93bbc9fd451c563501b5831c32bbca). Performance measurements below were taken on **22 October 2026**, using reference commit `011c9e6` and engine 0.1.47.

## Quick start on Windows

1. Download the portable ZIP and `SHA256SUMS.txt` from [Releases](https://github.com/aktalascloud/strata-avx1-p40/releases).
2. Verify the ZIP with `Get-FileHash -Algorithm SHA256`, then extract it to a short, writable path, such as `C:\Strata-P40`.
3. Run **`INSTALL.cmd`**. It checks prerequisites, downloads the pinned GGUF, vision projector, and MTP files from Hugging Face with **resume support and SHA-256 verification**, then builds a local pack directly from the GGUF. The original checkpoint is not required.
4. Run **`START.cmd`**. It starts Strata through a separate Windows scheduled task. Use **`STOP.cmd`** for a verified graceful shutdown; if a request is busy, let it finish and retry.
5. Open `http://127.0.0.1:8093/`. The OpenAI-compatible API base URL is `http://127.0.0.1:8093/v1`.

Use the CMD files from the release archive for this AVX1/P40 build. `CHECK.cmd` verifies the package without downloading a model, starting a server, or registering a task.

No model weights, generated packs, API keys, personal configurations, logs, caches, compilers, or SDKs are included. Microsoft Visual C++ Runtime is downloaded directly from Microsoft if needed, and its signature is checked. Install a P40-compatible NVIDIA driver with CUDA 12.9 support separately.

Downloads total approximately **85.6 GB**. Allow roughly **100 GB of free storage**, including the generated pack. The reference system had **256 GiB of RAM and 24 GiB of VRAM**; smaller memory configurations have not been qualified.

For the tested 16-thread system with the GPU on NUMA node 0:

```bat
INSTALL.cmd --workers 14 --numa-node 0
```

Confirm your GPU's NUMA node before selecting it. The generic installer leaves NUMA preference **off** by default. You can choose a separate directory for the downloaded weights with `--models-dir`.

## Measured performance

Reference hardware: **2 × Xeon E5-2697 v2**, 16 visible logical CPUs, 256 GiB RAM, **Tesla P40 24 GiB**, Windows x64, NVIDIA driver 582.70. The build uses Clang O3 with Ivy Bridge tuning and CUDA 12.9 for **sm_61**.

| Workload | Engine decode | Whole-request API rate | First reasoning token |
|---|---:|---:|---:|
| Short prompt, 128 generated tokens | 50.2789 tokens/s | 47.6324 tokens/s | 0.172 s |
| Cached 4K context, 128 generated tokens | 49.9454 tokens/s | 47.0583 tokens/s | 0.188 s |

Fresh 4K prompt processing was measured separately at **262.25 tokens/s**. Throughput with a fully occupied 128K context was **not measured**. Thinking tokens are included in the generated-token count.

### Controlled comparisons

| Comparison | Before | After | Measured change |
|---|---:|---:|---:|
| IQ staging, QFUSE, and GR fast path together | 47.9760 tokens/s | 50.4235 tokens/s | **+5.101%**, or +2.4475 tokens/s |
| B6 + EXPDEC, I64/J96 | 48.7498 tokens/s | 50.1116 tokens/s | **+2.793%**, or +1.3617 tokens/s |
| 14 versus 8 CPU workers, NUMA node 0 | 47.9257 tokens/s | 49.5107 tokens/s | **+3.307%** |
| NUMA node 0 preference versus default allocation | 48.8009 tokens/s | 49.5107 tokens/s | **+1.454%** |

These scores are harmonic means of two per-workload medians. The comparisons came from separate sweeps: **do not add or multiply their gains**. Each arm used two warmups and five measured requests per workload, 128 generated tokens, temperature 0, seed 12345, and the author's high/xhigh reasoning mode.

The first installation produced 16.4 tokens/s with different KV, context, MTP, thinking, and cache settings. That historical result is not a controlled baseline for attributing gains to individual patches.

[All 16 kernel combinations and methodology](p40/BENCHMARKS.md) · [Structured results](p40/results/benchmarks.json)

## Patches and selected settings

| Component | Purpose |
|---|---|
| [`native-ivybridge-p40.patch`](p40/patches/native-ivybridge-p40.patch) | Clang O3/Ivy Bridge baseline without AVX2, FMA, or F16C in the baseline path; optional CPU pinning disable; Windows NUMA memory preference; additional CPU and CUDA Graphs correctness checks. Already applied to this fork. Wider kernels retain their ISA guards. |
| [`pascallama-sm61.patch`](p40/patches/pascallama-sm61.patch) | Pascal DP4A MMQ tuning with J96 tiles and loop-unrolling hints, applied only to a private copy of the pinned GGML dependency. Based on [pascallama.cpp](https://github.com/madsteph74/pascallama.cpp). |
| B6 = 1, EXPDEC = 1 / R = 1, I64/J96 | The selected combined kernel configuration. B6 value 1 selects two rows. |
| IQ staging, QFUSE, and GR normalization fast path | Enabled together after direct and CUDA Graphs checks. Several fast paths already exist in upstream Strata. |
| DenseF32 | Experimental. All 5,201 standard correctness cases passed; the observed 0.12% prefill difference is within measurement noise. |

The runtime preset keeps **131,072 tokens, KV q4_0, author xhigh, MTP Q2 with two draft tokens, prefill 512, PLE in RAM, PCIe auto, and CPU-only vision**. MTP uses `--spec 3` and `--spec-min-p 0.25`. Expert dropping is disabled.

PGO, ThinLTO, extra CUDA vectorization, and I128 were tested separately and in combinations. Ordinary O3 with I64/J96 was selected. No isolated performance percentage is claimed for every patch hunk.

The reference build passed **22 numerical and graph checks**, including the full 5,201-case DenseF32 sweep. Other GPUs and backends are not qualified by this Windows release. The preset does not change CPU affinity, clocks, power limits, fans, or thermal protection.

[Patch descriptions and individual comparisons](p40/PATCHES.md) · [Reviewed external sources](p40/RESEARCH.md)

## Licenses and credits

Strata and its source modifications retain the **MIT license** and upstream copyright notices. Third-party binaries retain their own terms; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and the included license files. Model licenses apply separately to files downloaded from their publishers.

- [Original Strata](https://github.com/Niko1221/Strata)
- [Pascal MMQ patches](https://github.com/madsteph74/pascallama.cpp)
- [GGUF model](https://huggingface.co/DavidAU/Qwen3.8-Flash-Next-Abliterated-Uncensored-Turbo-Brilliance-50x-Reasoning-Instruct-GSQ-RCO-GGUF)
- [MTP files](https://huggingface.co/Maximilian228/Qwen3.8-Flash-Next-NVFP4-GPTQ-Strata)

This is an independent community build. It is not endorsed by the upstream authors, NVIDIA, or Microsoft.
