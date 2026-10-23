# Numerical qualification sources

The native aggregate adds CPU/no-pin/NUMA/Pascal graph screens; upstream contains
the other CUDA/IQ/GR parity targets. The generator here is the numerical-only
B6/EXPDEC/actual-IQ-MMQ driver generator with repository paths adapted for this
fork. Source SHA pins, count/ISA/SM/uniqueness/SRAM checks and numerical bounds
remain enforced. Run it with --root <this-repo> --build <repo/work/build-dir>
--output <new-repo/work/checks-dir> --cuda <CUDA12.9-directory>; never overwrite a live check package.
Private Windows CRLF versus public Git LF is reviewed by comparing every source
body after EOL normalization; public SHA pins match the actual LF source bytes.

The selected deployment ran22 cases: the previous16 (including the full standard
5201 DenseF32 GEMM sweep), one actual-IQ MMQ test, three B6 modes, and two EXPDEC
grid/graph cases. Timing loops are disabled in the generated extra drivers.
The PowerShell policy gives exact runtime cases and argv. These files are source,
not raw logs or prebuilt test binaries. Building an engine alone is not qualification.
