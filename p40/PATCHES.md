# Active patches and settings

| Component | Purpose and selected behavior |
|---|---|
| `patches/native-ivybridge-p40.patch` | Reviewed aggregate already applied to the stated official source. Ivy Bridge O3/AVX1, no-pin option, application NUMA preference, author modes and correctness/security ports. Wide kernels retain ISA guards. |
| `patches/pascallama-sm61.patch` | Pinned Pascal DP4A MMQ J96/unroll on a private GGML build copy; I64/J96 selected. I128/J96 exceeds P40 SRAM and stays forbidden. |
| IQ staging, QFUSE, fast GR | Selected together after direct/Graph numerical checks. New upstream QFUSE quantization and one-token commit corrections retained. |
| B6=1, EXPDEC=1/R=1 | Selected combined profile; B6=1 processes two rows. |
| DenseF32 | Experimental, full 5,201 parity cases. Historical +0.12% prefill observation does not establish a speedup. |
| CPU2638 | Guarded IQ4_NL AVX dispatch, exact FP16 conversion without F16C, Q2 activation-sum reuse and explicit odd-tail zero lanes. |
| Guided/fused CPU scheduling | Both opt-in, OFF in production. Epoch/CAS, independent GGUF offsets and NUMA fallback retained. Guided retry lost 4.32% across two real Qwen workloads; microbench gains are not model gains. |
| Checkpoint pool and cache slots | New upstream bounded thread handles and moved checkpoint storage; selected synchronous park reuse without async DMA. Smallest-slot pressure eviction and unsigned budgets retained. Transient device tags are not capture identity. |
| Compact prefill scratch | One-expert-group MMQ scratch combined with new upstream WS allocation; direct/Graph parity retained. HC-region reuse remains OFF. |
| Serving and tool boundaries | Declared canonical tool names/aliases, safe thinking-budget cut and PR4314 boolean/fractional output-budget rejection. Protected admission/drain control retained. |
| Author modes/UI | Standard High/XHigh, separate Ultra/Adaptive; default Adaptive/Auto, original tokenizer. Stateless Mnemosyne-derived logic; no memory/DB/embedder. Russian default plus English and upstream catalogs. |
| Model-library portability | Separate pinned CPU/CUDA/Vulkan/Poly library, guarded grammar/JSON recursion and Vulkan views. Native Qwen keeps its own dependency/fast path. |
| Pillow 13 | Reviewed dependency security overlay; bundled runtime already fixed. Native and dependency qualification are separate. |

Preset: 131,072 tokens, KV q4_0, MTP Q2/two drafts (`--spec 3`, minimum probability 0.25), prefill 512, PLE RAM, PCIe auto and CPU vision. Ivy Bridge `-O3 -march=ivybridge -mtune=ivybridge`, no AVX2/FMA/F16C; CUDA 12.9/O3/sm_61, MSVC `/O2 /Ob3 /favor:INTEL64 /fp:precise`. No fast-math, PGO/ThinLTO or expert dropping. Affinity, system NUMA, clocks and power stay unchanged.

[First installation / latest selected measurement](BENCHMARKS.md) · [Qualification limits](INSTALLATION-VERIFICATION.md) · [Authors and reviewed ports](COMMUNITY-FIXES.md). CPU/GPU component effects come from separate controlled whole-model comparisons; percentages are never added. Hardware and trained-model support beyond the stated qualification remains experimental.
