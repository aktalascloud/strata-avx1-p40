# Current build

Official source `7dd5cf18e68c639a8773e096c5c79f971ea2a9f5`.

- Upstream Terminal 0.2.4.2 / custom engine 0.1.49.2: corrected installer execution, missing-script packaging, DeepSeek own-file/projector recognition and signed engine selection. DeepSeek remains disabled in this P40/Qwen build.
- The complete AVX1/P40 aggregate retains 11 earlier fixes and adds declared canonical-tool boundaries, the IQ3_S/Q2 benchmark repair and a tested optional CPU pool port. Extra unroll/cache/register/fused settings lost local comparisons; the proven O3/Pascal profile is retained.
- Explicit Ivy Bridge O3/AVX and CUDA 12.9/sm_61, Pascal MMQ/Graphs/B6/EXPDEC/IQ/GR, MTP Q2, 128K/Q4, PLE RAM and CPU vision are preserved. Only the original installation and latest source-pinned result are compared; no intermediate release/sweep tables.

Measured performance is independently source-pinned in BENCHMARKS.md.
