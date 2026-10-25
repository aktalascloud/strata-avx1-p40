# Strata · AVX1 / Tesla P40

[English](README.md) · [Русский](README.ru.md) · [Download](https://github.com/aktalascloud/strata-avx1-p40/releases/latest)

A Windows build of [Strata](https://github.com/Niko1221/Strata) for **Ivy Bridge Xeons and Tesla P40 (sm_61)**. Engine **0.1.49.3**, upstream [`7dd5cf18e68c`](https://github.com/Niko1221/Strata/commit/7dd5cf18e68c639a8773e096c5c79f971ea2a9f5). Reviewed patches, reproducible measurements, portable runtime.

Reference model: **DavidAU Qwen3.8-Flash-Next IQ3_S**, MTP Q2, CPU vision. No weights, keys, private settings, logs, caches, SDKs or compilers are included.

## Before / after

| Generation | First installation | Latest measurement |
|---|---|---|
| Engine tokens/s | 16.45 | 48.77 |
| Whole-request API tokens/s | 11.65 | 44.65 |

Latest measurement: **2026-10-25**, engine **0.1.49.3**, binary `45B99DC2`, source `7dd5cf18e68c`. Cached 4K: **50.15** engine tokens/s and **45.48** whole-request API tokens/s.

First installation: preserved historical cold 64-token measurement, 32K/FP16, no MTP or reasoning; the stock binary was not rerun. Latest: median of 3 warmed 128-token responses after 2 warmups; 128K/Q4, MTP Q2, xhigh, temperature 0, seed 12345. Settings differ: this is historical progress, not a simultaneous binary A/B or an isolated patch gain. Full 128K throughput was not measured.

Separate controlled whole-model experiments support CPU tuning (14 workers: +3.307%; NUMA 0: +1.454%) and GPU tuning (IQ/QFUSE/GR: +5.101%; B6/EXPDEC: +2.793%). Those effects were measured on `011c9e6`; never add them. Intermediate releases and sweep tables are omitted.

[Evidence and method](p40/BENCHMARKS.md) · [JSON](p40/results/benchmarks.json)

## Install

1. Download ZIP + `SHA256SUMS.txt` from [Releases](https://github.com/aktalascloud/strata-avx1-p40/releases). Verify with `Get-FileHash -Algorithm SHA256`; extract to a short writable path, e.g. `C:\Strata-P40`.
2. Install a P40-compatible NVIDIA driver supporting CUDA 12.9. Run **`INSTALL.cmd`**; approve elevation for this installation's startup/control tasks.
3. The installer downloads pinned GGUF, mmproj and MTP with **resume + SHA-256**, then packs GGUF directly. No original checkpoint. Downloads: approximately **85.6 GB**; allow **100 GB disk space**. Smaller RAM/VRAM systems than the reference were not qualified.
4. Run **`START.cmd`**. Panel: `http://127.0.0.1:8093/`; OpenAI API: `http://127.0.0.1:8093/v1`. **`STOP.cmd`** drains requests gracefully.

**Autostart is independent of Codex:** a Windows task starts 45 seconds after boot, before logon. `AUTOSTART.cmd` registers it again; `CHECK.cmd` checks the package without starting a server or downloading weights. Separate folders use separate task names.

```bat
INSTALL.cmd --workers 14 --numa-node 0
```

Use that NUMA choice only after checking your GPU's node; generic default is off. Optional `--models-dir` selects weight storage; `--port 8094` selects an unused port for a new installation. Existing settings are retained. After moving an installed folder, regenerate its local preset and register tasks for the new path.

## Build and preset

| CPU | CUDA / P40 |
|---|---|
| Clang 23.1.4, `-O3 -march=ivybridge -mtune=ivybridge` | CUDA 12.9, `-O3`, `CMAKE_CUDA_ARCHITECTURES=61` |
| Baseline: no AVX2/FMA/F16C, strict FP | MSVC host: `/O2 /Ob3 /favor:INTEL64 /fp:precise` |

[Native patch](p40/patches/native-ivybridge-p40.patch) is **already applied**; wider CPU paths retain ISA guards. [Pascal MMQ overlay](p40/patches/pascallama-sm61.patch) changes a private pinned GGML copy only. Preset: **128K, KV q4_0, xhigh, MTP Q2/two drafts (`--spec 3`), prefill 512, PLE RAM, PCIe auto, CPU vision**, B6=1/EXPDEC=1/R=1, I64/J96 and four IQ/GR switches.

PGO, ThinLTO, extra CUDA vectorization and I128 lost the reference comparisons. DenseF32 remains experimental; its +0.12% prefill observation does not establish a speedup. No expert dropping, affinity, power or clock changes.

[Current changes](p40/CHANGES.md) · [Reviewed contributions](p40/COMMUNITY-FIXES.md) · [External sources](p40/RESEARCH.md) · [Installation qualification and limits](p40/INSTALLATION-VERIFICATION.md)

## Licenses

Strata and source modifications retain **MIT** notices. Runtime dependencies retain their own terms: [third-party notices](THIRD_PARTY_NOTICES.md). Microsoft VC Runtime is obtained directly from Microsoft with signature verification. Downloaded model licenses apply separately: [GGUF](https://huggingface.co/DavidAU/Qwen3.8-Flash-Next-Abliterated-Uncensored-Turbo-Brilliance-50x-Reasoning-Instruct-GSQ-RCO-GGUF), [MTP](https://huggingface.co/Maximilian228/Qwen3.8-Flash-Next-NVFP4-GPTQ-Strata). Independent community build; no upstream/NVIDIA/Microsoft endorsement.
