# Reviewed community contributions

The native aggregate retains the earlier fixes and the reviewed ports below. Heads identify the exact reviewed inputs; a later PR update is reviewed separately. Strata/MIT notices and authorship are preserved.

| PR | Author | Pinned head | Change |
|---|---|---|---|
| [#1882](https://github.com/Niko1221/Strata/pull/1882) | @LeGeRyChEeSe | `dbc8eefb94b5` | Expose live context length under max_model_len and context_length in /v1/models. |
| [#1883](https://github.com/Niko1221/Strata/pull/1883) | @LeGeRyChEeSe | `2d9138d19dd3` | Suppress Windows console flashes for engine/vision children; preserve explicit creation flags. |
| [#2870](https://github.com/Niko1221/Strata/pull/2870) | @Eranicus30666 | `9b4e7e783fcc` | Send the final streamed usage chunk with choices=[] when include_usage is requested. |
| [#2955](https://github.com/Niko1221/Strata/pull/2955) | @sergqwer | `c52d60b31094` | Preserve BF16 quiet NaN instead of converting a NaN to infinity; finite rounding stays unchanged. |
| [#3385](https://github.com/Niko1221/Strata/pull/3385) | @j-luwierski | `9f4b65fca612` | Prevent PLE reader close/initialization failure hangs; test Windows reads/reopen with caller/threaded IO. |
| [#3625](https://github.com/Niko1221/Strata/pull/3625) | @HeimEndyd | `18aa617c3fd5` | Destroy each private CUDA stream on its owning device; restore the previous device and test thread-local lifetime. |
| [#3789](https://github.com/Niko1221/Strata/pull/3789) | @page1 | `0a11fbd9bf90` | Read Windows parent PID/creation time only for matching orphan candidates; retain identity checks. |
| [#1284](https://github.com/Niko1221/Strata/pull/1284) | @sergqwer | `7c2d43216b9b` | Reject non-finite adapt_decay and values outside the exclusive (0,1) interval; keep the current default. |
| [#1503](https://github.com/Niko1221/Strata/pull/1503) | @sanastasiou | `cef12c872b5d` | Clear retained K/V on cross-conversation reuse and slot copy; adapt to the fresh slot-shuttle caller. |
| [#3676](https://github.com/Niko1221/Strata/pull/3676) | @yang478 | `229034673809` | Greedy requests do not inherit default penalties that disable MTP; explicit penalties and normal sampling stay intact. |
| [#2672](https://github.com/Niko1221/Strata/pull/2672) | @page1 | `aaaefd6e4c0c` | Windows guarded startup: prefault normal pages before CUDA registration, parallel dense uploads, early arena reads with RAM headroom. No throughput gain claimed. |
| [eddoursul/StrataFast#16](https://github.com/eddoursul/StrataFast/pull/16) | @txiki739 | `0dd8667edc88` | Optional single-phase native CPU pool; current epoch, layout and NUMA semantics retained. |
| [Niko1221/Strata#3871](https://github.com/Niko1221/Strata/pull/3871) | @Licenser | `2fb22d1278e7` | IQ3_S benchmark crash fix and actual Q2 pool-path timing; no production quantizer change. |
| [toddballinger/Strata-5080#16](https://github.com/toddballinger/Strata-5080/pull/16) | @toddballinger | `c649e492ab6c` | Declared canonical tools only, including streamed and truncated calls. |
| [#3945](https://github.com/Niko1221/Strata/pull/3945) | @ruibeikaa | `b6cc889913ec` | Checkpoint capture identity and buffer moves, with local allocation-failure guards. |
| [#3971](https://github.com/Niko1221/Strata/pull/3971) | @macintog | `ec7c95fc90df` | Preserve safe in-flight thinking tokens at a budget cut. |
| [#3972](https://github.com/Niko1221/Strata/pull/3972) | @Righteous-AI | `6f5d5ab35b4c` | Unambiguous declared namespace-tool spellings; canonical names still govern. |
| [#3973](https://github.com/Niko1221/Strata/pull/3973) | @wannagoxuf | `d604729e0428` | Retained-KV byte-identity regression. |
| [#4011](https://github.com/Niko1221/Strata/pull/4011) | @SuperDistance | `ae5aa79bdeb2` | Explicit UTF-8 CMake version parsing on Windows. |
| [#4031](https://github.com/Niko1221/Strata/pull/4031) | @dsenchankau | `d31e52352179` | Partial: smallest unpinned slot victim and budget-underflow guard; no automatic RAM-limit shrinking. |
| [#4039](https://github.com/Niko1221/Strata/pull/4039) | @merbanan | `c4dd0af3cb78` | Compact per-group MMQ scratch; HC-region reuse remains off. |

CPU fused scheduling follows the StrataFast/txiki739 work, itself based on Francesco Albano's Hardin22 implementation. It remains off in the selected profile. The checkpoint and compact-MMQ ports add ownership and direct/graph numerical checks; these checks do not establish an isolated tokens/s gain.

## Decisions

- GP100-only HFMA2/no-DP4A kernels, SM70/SM80+ Tensor Core paths, multi-GPU placement and Linux-only NUMA operations are not blindly enabled on Windows/P40.
- CPU row deferral (official PR2690) intentionally changes outputs; excluded.
- StrataFast draft-proxy changes target a separate component absent from this official native MTP path.
- Older staged-prefill gathering patches require a port to the newer dynamic ring/direct-MMQ layout and dedicated parity; an old fixed-slot mask is not applied to it.

[Current patches](PATCHES.md) · [Source review scope](RESEARCH.md) · [Original/latest performance](BENCHMARKS.md). Correctness tests do not establish an isolated speed gain for every fix.
