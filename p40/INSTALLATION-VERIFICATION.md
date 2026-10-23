# Portable installer verification

Verified on **23 October 2026** on the reference Ivy Bridge / Tesla P40 Windows system.
This was a fresh installation directory with spaces in its path, outside the maintainer's working project. It was not a fresh Windows installation or a reboot test.

| Check | Result |
|---|---|
| Published ZIP identity and extraction | Published SHA-256 matched; original package integrity check passed. |
| Model inputs | All seven GGUF, projector, and MTP inputs independently verified against their pinned SHA-256 values. Existing downloads were exposed as NTFS hard links; no model bytes were downloaded again. |
| Pack and tokenizer | Generated directly from the GGUF by the bundled Python; no original checkpoint, working pack, or personal configuration copied. |
| Clean runtime environment | Both native executables reported their versions with a system-only PATH. NumPy, Pillow, psutil, Jinja2, and regex loaded from the extracted package. Private Python, CUDA, and Strata environment settings were removed. |
| Installation paths | Generated configuration, Python, native engine, CPU vision, tokenizer, pack, and model paths all resolved inside the new directory. |
| Independent launch | START.cmd returned before readiness. Task Scheduler owned the launcher; every server, engine, and vision process was outside the caller's Codex Job object. |
| HTTP routes | UI, health, model list, status, and OpenAI-compatible chat API responded on the selected alternative port, 8094. |
| Real model request | One synthetic image request passed through the CPU projector and GPU model and generated eight tokens. This was a functional smoke test, not a speed benchmark. |
| Autostart | Actual registered tasks read back as S4U / least privilege, with a 45-second BootTrigger, no execution time limit, IgnoreNew, and hard termination disabled. The same startup action was exercised manually. No interactive logon or Codex process is required by the task definition. |
| Shutdown and restoration | Schema3 graceful drain completed without cancellation or force kill. The production model was restored; its configuration, active runtime, launcher, bootstrap, and control-review hashes were unchanged. Test tasks were removed. |
| Offline checks | Ten installer tests and six task-definition/guard checks passed. |

The test found and fixed two packaging defects: the original task had no boot trigger, and the original bootstrap forced port 8093 instead of using the local preset. Installer revision r2 includes both fixes, isolated task names and control tasks, and preserved CMD failure exit codes.

Limits: the operating system and Codex were not restarted or closed during the test. Independence was established from actual scheduler ancestry and Job membership. Existing NVIDIA and Microsoft runtimes satisfied the declared system prerequisites; the missing-runtime installation branch was not exercised on this host. Full network model downloads were not repeated; resumability and corruption handling were checked with the offline HTTP fixtures.


## Source0.1.48 /5c8dd322 follow-up

The table above describes the earlier source011c9e6/r2 clean-folder test. New source5c8dd322 and its exact engine/vision bytes passed fresh CPU/ISA/private-DLL qualification and23 numerical/graph GPU runs, including the full5201-case DenseF32 sweep and BF16 bit parity. It was loaded through the independent private S4U task with128K/Q4/MTPQ2/CPU vision and all selected settings preserved. No new-source model generation or throughput benchmark was run.

One control helper changed: native Windows engine children may own a canonical System32 conhost.exe with the exact0x4 argument. Acceptance requires an exactly identified native parent in the captured owner tree and valid creation order. Unknown executables, paths, arguments, parent identities, restricted parents and earlier creation times remain rejected. The12 portable policy tests cover these decisions. This function, full owner verification and controlled drain have the same AST as the private helper that completed an actual schema3 graceful stop and independent restart on the new engine. No force kill, bootstrap/review overwrite while alive, DACL change or admission/drain guard bypass occurred.

All other installer/launcher/bootstrap/scheduler helper bytes remain identical to r2. Their earlier clean-folder/boot-definition qualification is reused; offline installer/task/import/package checks were rerun. The full public clean-folder/model test, OS reboot, Codex-close test and85GB network transfer were not repeated.
