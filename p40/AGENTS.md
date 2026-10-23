# P40 kit maintenance

This directory contains the AVX1/P40-specific release helpers and measured results.
Keep source MIT notices and separate binary dependency licenses. The Pascal patch's
MIT declaration is in the pinned upstream README, reproduced in licenses/.

Never commit model weights, generated packs, live configurations, credentials,
launch receipts, logs, caches, local paths or hardware owner identities. Export
aggregate benchmark measurements, not private prompts or responses.

The native aggregate is already applied in this fork. The Pascal patch applies
only to the pinned build-local GGML copy. Do not apply historical patches again.
Keep ISA/SM/uniqueness/SRAM checks and exact numerical tolerances. Other backends
are not qualified by the Windows P40 release.

Preserve the distinction between the measured reference source and the current
release source. A new correctness-qualified binary is not automatically faster.
Do not add percentages from separate sweeps or fabricate per-patch attribution.

Merge official upstream main with normal Git ancestry, review conflicts by meaning,
retain new upstream behavior, then update the patch manifest and source pins after
review. Never use force push, reset a published branch, or accept all ours/theirs.
Keep raw upstream bench/results and experimental model artifacts out of the current
tree. No logs or model files belong in this kit's release.

CMD files in windows/ are release-root templates. Test helpers offline with tiny
local HTTP fixtures; never download a second large model just to test the installer.
