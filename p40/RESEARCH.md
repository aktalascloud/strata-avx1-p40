# Sources reviewed

Review date: 24 October 2026. Metadata inventory is separate from detailed code review.

- GitHub exposed 3,266 accessible Strata forks; 3,089 were active or starred. All open and the latest 100 closed PRs were collected for 114 applicable repositories, including official Strata: 1,194 PR entries, with duplicates across forks.
- Forty-three high-signal fork branches were selected for file-list comparisons. Twenty-six comparisons were available; 17 older/orphaned histories lacked a common ancestor. Their metadata and selected pinned sources are treated separately; no unrelated-history merge is performed.
- Sixteen targeted PRs received pinned file/hunk inventories; selected production ports were reviewed separately. Changes and exact heads are in [COMMUNITY-FIXES.md](COMMUNITY-FIXES.md). This is not a line-by-line audit of thousands of forks.
- Global GitHub searches covered AVX1/Ivy Bridge, no-AVX2, Pascal/P40, CUDA and LLM inference. Earlier source reviews also covered the 26 repositories supplied by the user.

| Source | Applicability |
|---|---|
| [StrataFast CPU pool](https://github.com/eddoursul/StrataFast/pull/16) | One-phase expert scheduling; ported to current epoch counters, per-job layouts and NUMA fallback; 360 bitwise CPU cases. Selection still requires local throughput evidence. |
| [Official CPU benchmark fix](https://github.com/Niko1221/Strata/pull/3871) | Fixes IQ3_S test-data generation and Q2 path attribution. |
| [Declared-tool boundary](https://github.com/toddballinger/Strata-5080/pull/16) | Security port, retaining current canonical aliases; parser/API tests pass. |
| [CPU deferral](https://github.com/Niko1221/Strata/pull/2690) | Rejected: intentionally changes model outputs and reports nonzero KL. |
| [Ivy Bridge LLM](https://github.com/jmcglock/ivy-bridge-llm) | AVX1 MoE fallback and deployment notes for Gemma/ik_llama Q8; not a drop-in IQ3_S Strata kernel. |
| [Pascal patch set](https://github.com/sbendhiba/llama-cpp-pascal-patches) | 41 pinned patches screened by target and call path. GP100 HFMA2/no-DP4A paths do not match P40; llama graph/sampler changes do not run in Strata's native backend. |
| [MiniCPM5 Pascal kernels](https://github.com/ArtyomITA/minicpm5-kernel-pascal) | Bitwise Q8 projection/dequantization work; graph-specific MiniCPM kernels and f16 KV advice do not directly replace this IQ3_S/Q4 Strata path. |
| [fp16-fixer](https://github.com/christopherrobertbrooks-tech/fp16-fixer) | PyTorch model-overflow repair, tested on V100; not a Strata speed patch or a reason to replace correct FP32 paths on P40. |
| [Pascal stack](https://github.com/jpsanders/pascal-llm-stack) | Linux driver/toolkit deployment notes; not Windows native-kernel patches. Hardware support claims must be checked against NVIDIA documentation. |
| [pascallama](https://github.com/madsteph74/pascallama.cpp) | The active pinned DP4A MMQ overlay. |
| [P40 engine bakeoff](https://github.com/sarge18/p40-llm-engine-bakeoff) / [MMQ autorunner](https://github.com/cycle-five/pascal-mmq-autorunner) | Tuning methodology; other models and contexts do not establish gains for this model. |

Only locally qualified code and selected settings are enabled. No NVIDIA/AMD/Intel architecture guard, shared-memory bound, numerical tolerance or dependency pin is removed to make a patch compile. No foreign driver or service setup script is executed.
