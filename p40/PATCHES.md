# Active patches and settings

| Component | Purpose and evidence |
|---|---|
| `patches/native-ivybridge-p40.patch` | Already applied. AVX1/Ivy Bridge O3, optional pinning disable, Windows NUMA memory preference, correctness checks and reviewed community fixes. Wider CPU kernels keep ISA guards. |
| `patches/pascallama-sm61.patch` | Pinned Pascal DP4A MMQ J96/unroll overlay, applied only to a private GGML copy. I64/J96 is selected; I128/J96 exceeds the P40 shared-memory limit. |
| IQ staging, QFUSE, fast GR | Selected together after numerical and CUDA Graphs parity. |
| B6=1, EXPDEC=1/R=1 | Selected combined configuration. B6=1 means two rows. |
| DenseF32 | Experimental; all 5,201 numerical cases pass. Its earlier +0.12% prefill observation does not establish a speedup. |
| Native CPU fused scheduling | Semantic port of StrataFast PR16. Epoch/CAS claims, per-job GGUF offsets, dimensions and NUMA fallback are preserved. Runtime selection requires a measured gain; 360 CPU cases compare bitwise. |
| Declared-tool boundaries | Completed and streamed tool events require a declared canonical name. Current namespace aliases are preserved. |
| CPU benchmark correctness | Official PR3871 fixes an IQ quantizer null call and measures Q2 on the pool's actual path. It does not change production quantization. |
| Checkpoint ownership and cache slots | PR3945 moves checkpoints with matching capture identities; a bounded PR4031 port keeps larger conversations under slot pressure. Added allocation/identity guards and 576 ownership cases. |
| Compact prefill scratch | PR4039 reduces MMQ scratch to one expert group. Whole/compact outputs are compared bitwise in direct/CUDA Graphs at the model's matrix sizes. HC-region reuse remains off. |
| Thinking and tool names | PR3971 preserves safe in-flight thinking tokens at a budget cut; PR3972 recognizes unambiguous declared namespace aliases. No OWUI changes. |

| Model-library portability | Separate pinned library, explicit BMI2/AVX2/FMA/F16C off, CPU/CUDA/Vulkan workers and native NextN/head/shard checks. Native Qwen keeps its own dependency and fast path. |
| Parser and Vulkan fixes | Bounded grammar/JSON recursion and non-compute Vulkan view handling. Build copies are source-pinned; allocation, shader addressing and device-feature guards are preserved. |

| Ivy Bridge CPU2638 | IQ4_NL down dispatch uses the existing AVX GGML dot; Q2_0 keeps its native kernel. Two-row NT1, exact FP16 bit conversion without F16C and shared Q2_0 activation sums; odd-tail upper lanes explicitly zeroed. CPU numerical checks passed, no fresh whole-model speed measurement. |

The preset keeps 131,072 tokens, KV q4_0, author xhigh, MTP Q2/two drafts (`--spec 3`, `--spec-min-p 0.25`), prefill 512, PLE RAM, PCIe auto and CPU vision. Expert dropping is off. Affinity, system NUMA policy, clocks and power are unchanged.

[Original installation versus latest result](BENCHMARKS.md) · [Measured record](results/benchmarks.json) · [Authors and pinned PRs](COMMUNITY-FIXES.md). Component effects come from separate controlled whole-model experiments; never add them. Numerical correctness and throughput are separate evidence.
