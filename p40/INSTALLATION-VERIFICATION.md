# Installation and runtime verification

Qualified source: [`7dd5cf18e68c`](https://github.com/Niko1221/Strata/commit/7dd5cf18e68c639a8773e096c5c79f971ea2a9f5), custom engine **0.1.49.3**. Qualification applies to the exact native/DLL fingerprints in source provenance, not every machine with similar hardware.

| Evidence | Scope |
|---|---|
| Native correctness | CPU/ISA/no-pin/lifetime checks, 4,789 cache cases, 576 checkpoint-ownership cases, 360 bitwise fused-pool cases and 25 numerical/graph GPU runs. Includes full 5,201-case DenseF32, BF16 direct/graph checks, retained-KV identity and compact-MMQ bitwise direct/graph comparisons. |
| Shared Python/API changes | 777 offline cases, five platform skips; 25 actual-Qwen tokenizer/decode and 15 reasoning-alias cases. The two known fixture modules passed all 25 focused reruns after declaring the Qwen-only mock catalog and custom version. Production ISA/admission guards remain unchanged. Full optional Terminal UI is outside the minimal API-runtime qualification. |
| Private live deployment | Exact schema3 drain, independent Windows-task launch, loaded API, context, CPU vision settings and owner proof. Direct text throughput is separately source-pinned in BENCHMARKS.md. |
| Current public package | Offline installer/resume/corruption, task-definition and console-policy tests; isolated imports, native versions, PS/CMD CheckOnly, source/library/privacy/license and ZIP CRC/SHA checks. No new 85 GB download or fresh-Windows claim. |
| Earlier clean-folder test | The r2 installer on source `011c9e6` was extracted into a separate path with spaces. All seven existing model inputs were hash-verified through hard links, a new pack was generated from GGUF, and a synthetic image request produced eight tokens on port 8094. This is an earlier functional smoke, not a new-source image benchmark. |
| Startup independence | Actual Task Scheduler ancestry and absence from the caller's Codex Job were checked. Registered S4U tasks had a 45-second BootTrigger, no time limit, IgnoreNew and hard termination disabled. The startup action was exercised manually; no OS reboot or Codex-close test was performed. |

Installer/bootstrap/task helpers retain their previous qualification only when their bytes are unchanged. The strict console-owner fix additionally passed 12 policy cases and a matching private live drain/restart. Only canonical System32 conhost0x4 under an exact wrapper/native parent is accepted; unknown or restricted identities remain rejected.

NVIDIA and Microsoft runtimes already existed on the reference host. The missing-VC-Runtime installation branch was not exercised there; the installer obtains it from Microsoft and checks Authenticode. No public clean-folder model/image run is claimed for every newly compiled engine. Other GPUs/backends and full-128K throughput remain unqualified by these results.

[Current performance evidence](BENCHMARKS.md) · [Changes](CHANGES.md) · [Reviewed contributions](COMMUNITY-FIXES.md)
