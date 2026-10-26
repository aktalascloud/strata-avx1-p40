# Verification and limits

Native engine **0.1.51**, official source [4b9e05a2a806](https://github.com/Niko1221/Strata/commit/4b9e05a2a806a3fe24f7b2560d98626c37dade35). Qualification belongs to exact EXE/DLL/source fingerprints.

- Native: CPU/ISA/no-pin/NUMA/lifetime checks,360 fused scheduling cases and25 numerical/graph GPU runs. Full5201 DenseF32 cases passed bitwise; BF16, actual-IQ MMQ, B6, EXPDEC, checkpoint identity and compact-MMQ checks are retained.
- Prior0.1.50 API/tokenizer scope:817 offline cases,8 skips. A staged-CLI fixture passed its focused rerun under a script-aware interpreter. One upstream documentation-title assertion remains failing; it is not a model/runtime failure and the suite is not advertised as all green. Existing Qwen tokenization and reasoning aliases match.
- Current0.1.51 frontend delta:8 unit/validation cases passed; no live model requests. Native CPU2638 rows/partition checks passed; exact candidate sources also retain their earlier2x65536 FP16-pattern proof.
- Live Qwen: schema3 drain without cancellation, immutable activation, independent Windows-task launch, loaded API,128K/Q4/MTP/CPU vision and exact owner verified. Only versioned executable/source/profile paths changed; sampler, model files and profile data stayed unchanged.
- Universal components: explicit Ivy Bridge O3/AVX1 without AVX2/BMI2/FMA/F16C; CUDA12.9/sm61. CPU and CUDA passed18 tensor cases each. MTP rejection/partial/full acceptance, repeated-state reset, seeded sampling, normal OpenAI API and SSE passed on synthetic untrained data. Parser-depth guards have real boundary tests.
- Vulkan: compiled worker and CPU/protocol checks; no Vulkan GPU was available on the reference host. RX580 hardware and trained GLM/DeepSeek runs remain pending. No new model downloads or speed tests were performed.
- Package: resumable-download/corruption, installer/task/console tests, clean-path offline installation, isolated imports/versions/PS+CMD CheckOnly, privacy/license checks and ZIP CRC/per-file SHA. Modified helpers have their own delta proof; unchanged task/control code retains exact prior proof only for identical bytes.

No fresh-Windows, real RX580, trained new-model, full128K throughput, reboot or Codex-close test is implied. Current native throughput was not remeasured; [performance evidence](BENCHMARKS.md) retains its actual measured source/version. The VC Redist missing-runtime branch was not exercised on the reference host; clients obtain it from Microsoft with Authenticode verification.
