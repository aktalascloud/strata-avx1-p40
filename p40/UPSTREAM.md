# Upstream integration and release policy

This is a source fork of Niko1221/Strata, not an unrelated engine. The original
history, copyright and MIT license are retained. Local native edits are exported
as a reviewable aggregate; Pascal changes remain a separately pinned GGML overlay.

The maintainer's daily08:00Asia/Bishkek task fetches official main, reviews the exact
diff and every local patch, adapts conflicts, then builds an inactive candidate.
The tested legacy CPU/GPU profile and all numerical checks must remain intact.
After a successful qualification/deploy, official changes are merged into the
public source branch and a new immutable release is published. Unchanged source,
patches and recipe do not cause duplicate rebuilds or releases.

Use a normal `git fetch upstream` and merge the real upstream commit. If the local
clone is shallow and a merge base is unavailable, deepen from the official source
until ancestry is known. Do not use an unrelated-history merge, force push or
replace fresh upstream files with old snapshots. Resolve ordinary conflicts by
preserving both the new behavior and the reviewed local change.

The current public tree deliberately omits upstream raw `bench/results/` data and
the optional experimental-speed-projection GGUF. Keep them excluded after merges.
The inherited official history is retained; no private working history is copied.
Own benchmark summaries belong only in p40/results/ and contain metrics, not logs,
conversation text, credentials, host names or private network addresses.

Release gates: exact source/binary fingerprints, full numerical/graph qualification,
offline installer tests, minimal runtime imports/version checks, license audit,
secret/host-data scans of source and binary tree, ZIP entry/CRC/hash verification,
and GitHub visibility/content/asset readback. A failed public-export gate stops
publication while the working private server remains untouched.
