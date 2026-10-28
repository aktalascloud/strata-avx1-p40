# Current build

Official source `46c152a1310f77cd2f0ce2c7cd213962df14fe83`.

- Native engine 0.1.53 with a real upstream merge; GB10/sm121 default/tile branches retained without selecting them on P40.
- Upstream ARM/Metal and Mac DeepSeek packaging improvements retained as source-only; not new P40 model qualification.
- Ivy Bridge O3, CUDA 12.9/sm61/L1-ca and the existing Pascal/control fixes preserved.
- Selected P40 Pascal Q8 main-only opt-in; MTP Q2 remains enabled. Latest pinned real API measurement 55.15 engine tokens/s, with warmed-workload limits.

Measured performance is independently source-pinned in BENCHMARKS.md.
