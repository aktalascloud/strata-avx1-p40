# Reviewed community contributions

The native aggregate retains the 11 earlier fixes and adds two runtime ports plus one benchmark-only repair. Heads below identify reviewed inputs; current source changes are adapted semantically rather than copied over newer files. Strata/MIT notices and authorship are preserved.

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

CPU fused scheduling follows the StrataFast/txiki739 work, itself based on Francesco Albano's Hardin22 implementation. The port adds bounded bitwise tests for worker/host modes, batch reset, oversized fallback and per-job GGUF offsets. The feature is enabled only if local measurement selects it.

## Decisions

- GP100-only HFMA2/no-DP4A kernels, SM70/SM80+ Tensor Core paths, multi-GPU placement and Linux-only NUMA operations are not blindly enabled on Windows/P40.
- CPU row deferral (official PR2690) intentionally changes outputs; excluded.
- StrataFast draft-proxy changes target a separate component absent from this official native MTP path.
- Older staged-prefill gathering patches require a port to the newer dynamic ring/direct-MMQ layout and dedicated parity; an old fixed-slot mask is not applied to it.

[Current patches](PATCHES.md) · [Source review scope](RESEARCH.md) · [Original/latest performance](BENCHMARKS.md). Correctness tests do not establish an isolated speed gain for every fix.
