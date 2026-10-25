# Verification and limits

Native engine **0.1.50**, official source [41cf05a06a25](https://github.com/Niko1221/Strata/commit/41cf05a06a25dd29103b7b27a2279a3f60c21876). Qualification belongs to exact EXE/DLL/source fingerprints.

- Native: CPU/ISA/no-pin/NUMA/lifetime checks,360 fused scheduling cases and25 numerical/graph GPU runs. Full5201 DenseF32 cases passed bitwise; BF16, actual-IQ MMQ, B6, EXPDEC, checkpoint identity and compact-MMQ checks are retained.
- API/tokenizer:817 offline cases,8 skips. A staged-CLI fixture passed its focused rerun under a script-aware interpreter. One upstream documentation-title assertion remains failing; it is not a model/runtime failure and the suite is not advertised as all green. Existing Qwen tokenization and reasoning aliases match.
- Live Qwen: schema3 drain without cancellation, immutable activation, independent Windows-task launch, loaded API,128K/Q4/MTP/CPU vision and exact owner verified. Only versioned executable/source/profile paths changed; sampler, model files and profile data stayed unchanged.
- Universal components: explicit Ivy Bridge O3/AVX1 without AVX2/BMI2/FMA/F16C; CUDA12.9/sm61. CPU and CUDA passed18 tensor cases each. MTP rejection/partial/full acceptance, repeated-state reset, seeded sampling, normal OpenAI API and SSE passed on synthetic untrained data. Parser-depth guards have real boundary tests.
- Vulkan: compiled worker and CPU/protocol checks; no Vulkan GPU was available on the reference host. RX580 hardware and trained GLM/DeepSeek runs remain pending. No new model downloads or speed tests were performed.
- Package: resumable-download/corruption, installer/task/console tests, clean-path offline installation, isolated imports/versions/PS+CMD CheckOnly, privacy/license checks and ZIP CRC/per-file SHA. Modified helpers have their own delta proof; unchanged task/control code retains exact prior proof only for identical bytes.

No fresh-Windows, real RX580, trained new-model, full128K throughput, reboot or Codex-close test is implied. Current native throughput was not remeasured; [performance evidence](BENCHMARKS.md) retains its actual measured source/version. The VC Redist missing-runtime branch was not exercised on the reference host; clients obtain it from Microsoft with Authenticode verification.
