# Numerical qualification sources

The native aggregate adds CPU/no-pin/NUMA/Pascal graph screens; upstream contains
the other CUDA/IQ/GR parity targets. The generator here is the numerical-only
B6/EXPDEC/actual-IQ-MMQ driver generator with repository paths adapted for this
fork. Source SHA pins, count/ISA/SM/uniqueness/SRAM checks and numerical bounds
remain enforced. Run it with --root <this-repo> --build <repo/work/build-dir>
--output <new-repo/work/checks-dir> --cuda <CUDA12.9-directory>; never overwrite a live check package.
Private Windows CRLF versus public Git LF is reviewed by comparing every source
body after EOL normalization; public SHA pins match the actual LF source bytes.

The selected deployment ran25 cases: the previous23 (including the full standard
5201 DenseF32 GEMM sweep and BF16 NaN parity), plus conversation_reuse_identity_test
and prefill_group_scratch_parity. The latter compares whole/compact MMQ outputs
bitwise in direct/CUDA Graphs at the model's matrix sizes. Actual-IQ MMQ, three B6
modes and two EXPDEC grid/graph cases are preserved. Configure conversation tests
with STRATA_BUILD_CONVERSATION_TESTS=ON; build the two additional CMake targets
before qualification. Timing loops are disabled in the generated extra drivers.
The PowerShell policy gives exact runtime cases and argv. These files are source,
not raw logs or prebuilt test binaries. Building an engine alone is not qualification.
