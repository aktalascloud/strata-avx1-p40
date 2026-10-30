# Current build

Official source `870aedd9e1ebe1c91f94da93b59af17729f6c5c0`.

- Official0.1.54, CUDA window8 explicit for legacyGPU footprint; widerHIP/SYCL changes retain their backend guards
- Conversation/expert cache late-allocation headroom and policy PLE lock handling; explicit PLE RAM preserved
- Quoted XML tool argument handling, family-specific end tokens and default declared-tool recovery; recovery remains bounded to declared names
- LocalUnicode UTF16pair correctness fix for damagedJSON containers; strictvalidJSON behavior unchanged
- RetainedAVX1/no-pin/Pascal/PCIeoverride/GGUFbounds/portableOpenAIID patches;3optionalcomponentCPU workspace/cvec fixes independentlyqualified

Measured performance is independently source-pinned in BENCHMARKS.md.
