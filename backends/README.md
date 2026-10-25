# Model backends

One Windows ZIP includes native Qwen, embedded CPU/CUDA/Vulkan and Poly CUDA workers.

See [models, MTP, installation and qualification limits](API-AND-MTP.md).
Native API ports are integrated into the aggregate; do not apply a historical API patch again.
The native and model-library dependencies have separate pins. Build-copy guards retain all ISA, SM, count, size and numerical checks.

DSV41/Engram remains a separate source experiment, disabled in the active Qwen recipe and excluded from this runtime ZIP.
No models, drivers or SDKs are bundled. No trained GLM/DeepSeek or RX580 performance claim is made.
