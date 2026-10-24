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

The preset keeps 131,072 tokens, KV q4_0, author xhigh, MTP Q2/two drafts (`--spec 3`, `--spec-min-p 0.25`), prefill 512, PLE RAM, PCIe auto and CPU vision. Expert dropping is off. Affinity, system NUMA policy, clocks and power are unchanged.

[Original installation versus latest result](BENCHMARKS.md) · [Measured record](results/benchmarks.json) · [Authors and pinned PRs](COMMUNITY-FIXES.md). Component effects come from separate controlled whole-model experiments; never add them. Numerical correctness and throughput are separate evidence.
