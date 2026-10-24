# Changes in this qualified build

Official source `06e51dfaef7003f01f23b85e63c800b10efe4066`, compared with `5c8dd322528cc84f68f461ad54a506b9da8fa8d4`.

- Official Terminal0.2.4 / Control0.1.49 adds a separate optional DeepSeekV4.1 engine and family-aware tokenizer, tool parser and reasoning handling. This P40/Qwen build keeps STRATA_BUILD_DSV41=OFF, downloads no new weights and does not claim DeepSeek hardware qualification.
- Qwen high/xhigh aliases and its actual prepared tokenizer were checked against the previously qualified source:25 tokenize/decode cases and15 reasoning-alias/budget cases match. Family/API/Control/setup regressions ran698 tests with5 skips and no failures or errors; dummy-engine fixtures use their documented simulated ISA floor.
- New CPU exact-row / trellis support retains ISA dispatch. The Clang compatibility patch adds VPOPCNTDQ/BMI2 only to the guarded IQ512 translation unit and requires BMI2 in that path's runtime predicate; Ivy Bridge baseline stays AVX without AVX2/FMA/F16C. Vendored Project Maya MIT license and attribution notice are preserved.
- All11 reviewed community fixes, O3/NUMA0/14workers, Pascal MMQ/Graphs/B6/EXPDEC/IQ/GR, MTPQ2/two draft tokens,128K/Q4, PLE RAM and CPU-only vision remain selected. CMake/this custom engine reports0.1.49; official Qwen prebuilt packages remain0.1.48. No new throughput claim.

No model/throughput benchmark was run for this update. Published rates remain tied to source011c9e6.
