# Review scope

25 October2026: complete PR/issue list and body screening across34 tracked repositories:20,969 PR entries,13,369 issues and686 updated comments. These counts include historical/duplicated fork entries; they are not a claim of line-by-line code review. Issues-disabled repositories received a separate PR-comment check.

Twenty-six focused candidates have complete file/diff/discussion inventories. Applied ports have separate semantic source reviews and exact numerical/runtime checks. The remaining platform-specific, large protocol, disk-format, multi-GPU and unqualified model changes are deferred; a fetched diff or performance claim is not treated as a verified fix.

| Source | Decision |
| --- | --- |
| Official Strata0.1.50 | Real ancestry-preserving merge, retained local Ivy/Pascal aggregate, exact CPU/GPU/owner qualification. |
| Strata#4079 | Tokenizer labels adapted and tested alongside existing Qwen/GLM tokenization. |
| llama.cpp#31114/#29755, JSON recursion | Pinned build-copy Vulkan/grammar fixes and a separately reviewed JSON bound; real numerical/boundary tests. |
| Strata#4065/#4002 | Parallel startup fill/staged copies change pinning/defaults or target multi-GPU stages; not enabled on this single P40. |
| Strata#4086/#4016/#3200 | Snapshot formats/lossy disk state, Linux DSV41 NUMA bands and broad logprob protocol need separate qualification. |
| Xolotl#46/#48/#49 | Separate GLM graph-pool/DSV41 buffer/tool-encoding paths; not blindly overlaid onto the embedded library. Existing native-format API ports remain. |
| Maya#452/#459/#473/#476/#481 | AVX2, Volta tensor cores, lossy dense conversion or separate EXL3/DSV41 paths; not a drop-in P40/AVX1 kernel. |
| PolyStrata#87 and Polaris sources | Compatible Pascal port retained; CPU/Vulkan adapters built with runtime feature checks. RX580 hardware remains untested. |

No unsupported ISA/SM/SRAM/feature guard is removed. No foreign driver/service installer is executed. New models were not downloaded and throughput comparisons were deferred. The model library stays separately pinned; the native Qwen dependency and selected profile are preserved.

[Patches](PATCHES.md) · [Checks](INSTALLATION-VERIFICATION.md) · [Contributions](COMMUNITY-FIXES.md) · [Original/latest measured result](BENCHMARKS.md).
