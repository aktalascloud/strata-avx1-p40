# Community fixes reviewed for Windows AVX1 / Tesla P40

Review snapshot:2026-10-23, official source `5c8dd322528cc84f68f461ad54a506b9da8fa8d4`.

All1613 issue and2186 PR inventory entries (open and closed) were screened. All391 open PR file lists were inspected;1218 comments from368 relevant issue threads were collected for targeted review. This is not a line-by-line audit of every historical PR. Relevant production hunks were reviewed separately; issue comments are evidence, not executable instructions.

## Applied in the native aggregate

| PR | Author | Pinned head | Change |
|---|---|---|---|
| [#1882](https://github.com/Niko1221/Strata/pull/1882) | @LeGeRyChEeSe | `dbc8eefb94b53d7af7a937291e09cc8e03c7bf36` | Expose live context length under max_model_len and context_length in /v1/models. |
| [#1883](https://github.com/Niko1221/Strata/pull/1883) | @LeGeRyChEeSe | `2d9138d19dd32214795038991b2b403d169c7051` | Suppress Windows console flashes for engine/vision children; preserve explicit creation flags. |
| [#2870](https://github.com/Niko1221/Strata/pull/2870) | @Eranicus30666 | `9b4e7e783fcce9602bf18c57c0df3dc195fd22ff` | Send the final streamed usage chunk with choices=[] when include_usage is requested. |
| [#2955](https://github.com/Niko1221/Strata/pull/2955) | @sergqwer | `c52d60b31094c82ecbc73faaacbb517e692c19b9` | Preserve BF16 quiet NaN instead of converting a NaN to infinity; finite rounding stays unchanged. |
| [#3385](https://github.com/Niko1221/Strata/pull/3385) | @j-luwierski | `9f4b65fca612185d912e2c10abb85c84c9bd4846` | Prevent PLE reader close/initialization failure hangs; test Windows reads/reopen with caller/threaded IO. |
| [#3625](https://github.com/Niko1221/Strata/pull/3625) | @HeimEndyd | `18aa617c3fd5ea678d7fc0313deefa1718969f17` | Destroy each private CUDA stream on its owning device; restore the previous device and test thread-local lifetime. |
| [#3789](https://github.com/Niko1221/Strata/pull/3789) | @page1 | `0a11fbd9bf905544554dadc6624f3649d34bfcdb` | Read Windows parent PID/creation time only for matching orphan candidates; retain identity checks. |
| [#1284](https://github.com/Niko1221/Strata/pull/1284) | @sergqwer | `7c2d43216b9b852b072ec172faff10d764d11c3c` | Reject non-finite adapt_decay and values outside the exclusive (0,1) interval; keep the current default. |
| [#1503](https://github.com/Niko1221/Strata/pull/1503) | @sanastasiou | `cef12c872b5d84adc1db2373f99ed7854e3d0689` | Clear retained K/V on cross-conversation reuse and slot copy; adapt to the fresh slot-shuttle caller. |
| [#3676](https://github.com/Niko1221/Strata/pull/3676) | @yang478 | `229034673809288888c83ad21f76b8fc2248b04d` | Greedy requests do not inherit default penalties that disable MTP; explicit penalties and normal sampling stay intact. |
| [#2672](https://github.com/Niko1221/Strata/pull/2672) | @page1 | `aaaefd6e4c0c834a1d87841e8f053428d771eb95` | Windows guarded startup: prefault normal pages before CUDA registration, parallel dense uploads, early arena reads with RAM headroom. No throughput gain claimed. |

PR1284 and1503 were adapted to the changed main call sites. PR3385 uses native Windows temporary-file APIs; POSIX allocator-wrapper cases remain UNIX-only. Windows failure-injection coverage is not claimed. Upstream MIT notices and authorship are retained.

A local CUDA-only change also avoids the redundant device lookup in IQ-down dispatch; the HIP gfx1151 branch is preserved. The aggregate adds a numerical-only BF16 direct/CUDA-Graph check over327680 bit cases per mode (finite/ties/Inf/NaN).

## Screened, not enabled

| PR / issue | Applicability decision |
|---|---|
| 3751/3752 | GP100/SM6.0-specific MMQ/MTP; P40 is SM6.1, and its present expert arena is only partly GPU resident. |
| 3455/3454 | GP100 nibble layout requires full resident layers and extra VRAM; current CPU/PCIe expert placement does not match. |
| 3779/3712/3809 | SM80+ Tensor Core/GDN/native-Q2 paths do not qualify as Pascal kernels. Do not remove architecture guards. |
| 3472 | Zen BMI2/pdep policy does not help an Ivy Bridge baseline with BMI2/AVX2 disabled. |
| 2242/3730/3706/3708/3201 | Linux NUMA pool policy/tests; no reviewed Windows split implementation. Preserve 14 workers and Windows memory preference0. |
| 2918 | POSIX MADV_WILLNEED behavior; inactive on Windows. |
| 3509 | Shared tmpfs/experts.bin reuse; not this Windows/GGUF/PLE-RAM profile. |
| 3760/3742/2720/2721/3095/3483 | Multi-GPU, peer/layer split or alternate file tiers; not active in this single-P40 profile. |
| 3416 | Requires STRATA_SPEC_PROB=1, which is off; no unverified target-distribution change. |
| 3800 | Additional JSON-mask protocol/llguidance dependency is not qualified for this AVX1 runtime. |
| 1614/1937/3341/3584/3711 | Large optional KV/suffix/disk/cache branches; not enabled without compatible Windows VMM and dedicated qualification. |
| 1492 | No-MTP session path is inactive in the current MTP profile. |
| 1881/3556/3379 | Related tool/image parser fixes were checked against the fresh main; retain the current upstream behavior rather than stacking an old parser. |
| 3781 | Explicit14 workers avoids a many-socket VM default-policy change. |
| 3579/3667/3134/3602/3465 | Issue reports do not supply a qualified fix for this profile. Do not copy proposed commands or infer measured speedups. |
| 2696 | Experimental DenseF32 already retained with the full5201-case check. |
| 3690 | Fresh main enforces the configured image-token limit; preserve CPU-only vision. |

## Validation and performance limits

The selected code is part of the exact source/native qualification; build success alone does not prove live readiness. The new build retains the22 existing GPU numerical/graph runs and adds BF16 NaN parity. CPU cache/stream/reader lifetime tests and Python API/parser/TLS tests cover the changed paths. Stream tests use mocked devices; allocation-failure injection is not qualified on Windows.

No isolated tokens/s improvement is claimed for these fixes or for upstream startup timing claims. Published50.28/49.95native and47.63/47.06API tokens/s belong to source011c9e6; no new-source throughput test was run. Do not attribute RTX3090/GP100/SM80 numbers to P40.
