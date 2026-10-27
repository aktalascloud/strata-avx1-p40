# Current build

Official source `4b9e05a2a806a3fe24f7b2560d98626c37dade35`.

- Runtime security revision: bundled Pillow 13.0.0 fixes GHSA-78g4-xqwv-q3g8; official PyPI cp313 Windows wheel SHA-256 verified, licenses retained.
- Native 0.1.51 and official source 4b9e05a2 are unchanged. The qualified engine, CPU vision and four optional workers are reused byte-for-byte; no new throughput claim.
- Changed-dependency checks: seven CPU codec roundtrips, seven Vision.normalize formats and EXIF rotation, plus twenty existing vision unit cases. No model or speed requests.

Measured performance is independently source-pinned in BENCHMARKS.md.
