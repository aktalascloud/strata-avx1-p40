# Effective patches and settings

Two patch files are shipped. The native aggregate is already applied to this fork; do not apply it twice.
The Pascal overlay is applied only to a private build copy of the pinned GGML dependency.

| Patch / setting | Purpose | Measured gain / limit |
|---|---|---|
| `native-ivybridge-p40.patch` | Clang O3/Ivy Bridge baseline, no AVX2/FMA/F16C; no-pin opt-out; Windows NUMA arena; CPU/no-pin and Pascal graph correctness tests. Wider kernels retain ISA dispatch guards. | Infrastructure aggregate; no honest isolated percentage for every hunk. |
| `pascallama-sm61.patch` | Full pinned J96 DP4A MMQ configuration and unroll overlay from madsteph74/pascallama.cpp. Keeps original GGML unchanged. | Included in all final controlled rows; no isolated causal percentage claimed. |
| IQ tables/MMVQ + QFUSE + GR_NORM_FAST, all1 | Upstream native kernel paths qualified in direct and CUDA Graphs modes. |47.9760 ->50.4235 harmonic tok/s, +2.4475tok/s /+5.101% in its own fresh sweep. |
| B6=1 alone | Existing Strata switch, I64/J96. |48.7498 ->49.5174tok/s, +0.7676tok/s /+1.574% in kernel-combination sweep. |
| EXPDEC=1/R1 alone | Existing Strata switch, I64/J96. |48.7498 ->48.9849tok/s, +0.2351tok/s /+0.482% in kernel-combination sweep. |
| B6=1 + EXPDEC=1/R1 | Selected combined kernel configuration. |48.7498 ->50.1116tok/s, +1.3617tok/s /+2.793%. |
|14 versus8 workers, NUMA0 | CPU pool tuning on16 visible logical CPUs. |47.9257 ->49.5107tok/s, +3.307%. Hardware-specific. |
| NUMA0 preference versus off | Local expert arena memory allocation; no affinity/CPU Sets change. |48.8009 ->49.5107tok/s, +1.454%. GPU was on node0. |
| DenseF32=1 | Experimental cuBLAS12.9 FP32 dense path. |5201 standard cases passed bitwise; observed +0.12%prefill is within noise, not demonstrated speedup. |
| PLE RAM, async1, PCIe auto, MTP Q2/spec3/minp0.25 | Selected runtime configuration; no expert dropping. |No isolated causal percentage claimed for each switch. |
| PGO, ThinLTO, extra CUDA vectorization | Tested separately and together. |Slower than ordinary O3 in the controlled sweep; not enabled. |
| I128 | Tested alone and in all B6/EXPDEC combinations with legal shared-memory tiles. |Best I128 score49.9366 < selected I64 score50.1116; not enabled. |

These are local measurements, not sums of upstream marketing claims. CUDA Graphs, B6/EXPDEC and several fast paths already exist in upstream; this kit contributes qualification, configuration, build fixes and local patches, with attribution.

The22 numerical/graph runs preserve the previous16 (including full5201DenseF32), actual-model MMQ, three B6 modes and two EXPDEC grids. Numerical-only qualification is separate from throughput tests. Do not weaken ISA/SM/uniqueness/SRAM guards or FP tolerances to make a candidate pass. Other GPUs/HIP/SYCL/Metal are not qualified by this release.
