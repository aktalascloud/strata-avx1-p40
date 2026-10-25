# Experimental model API and native MTP

The working Qwen/P40 runtime is independent of this source work. No model weights, startup tasks or live profiles
are installed by these tools. The current Windows release remains the qualified Qwen package.

## What is prepared

- A separate official model library at `b9acf138a1e28ce1fc23b5a4fc4b12444b50f7ea`, including merged
  [GLM5Next MTP PR29928](https://github.com/ggml-org/llama.cpp/pull/29928). The production dependency stays pinned separately.
- Embedded CPU, CUDA sm61 and Vulkan workers; no separate llama-server is installed.
- `api-compat.patch`: GLM tokenization/native tool calls, DeepSeek V4 DSML and author templates,
  OpenAI Chat Completions/Responses/SSE, authorization and backend-specific sampler arguments.
- A local GGUF profile preparer with bounded metadata reads, native-head validation and explicit GPU selection.

CPU fixture checks cover actual NextN proposals, rejection/partial/full acceptance, repeated-request state reset,
and equal greedy tokens with speculation off/on. The real CPU worker also passed normal and SSE OpenAI requests.
These are synthetic checks, not trained GLM/DeepSeek results or speed measurements.
The installed Qwen tokenizer and its author effort templates match the previous frontend exactly.
RX580 was not present on the reference host: its hardware checks remain outstanding.

## Inactive source checkout

Never patch a running installation or immutable runtime snapshot. Use a separate source checkout matching
`api-compat-review.json`; do not overwrite newer upstream files or rewrite review hashes to pass a guard.

```sh
python backends/verify-api.py --root .
git apply --check backends/api-compat.patch
git apply backends/api-compat.patch
python backends/verify-api.py --root .
```

The verifier is read-only. A matching candidate still needs its new exact schema3 control review and normal
deployment gates. The patch keeps admission, authentication, drain and control handlers unchanged;
main changes its tokenizer loader and adds a port guard only for explicit optional profiles. Native Qwen keeps its existing argument/sampler/preset path.

## Source build

```sh
python backends/fetch-library.py
cmake -C backends/ivybridge-cache.cmake -S backends/ggml -B backends/build-models -DSTRATA_LLAMA_SOURCE=/absolute/path/to/backends/.deps-models -DSTRATA_LLAMA_PIN=b9acf138a1e28ce1fc23b5a4fc4b12444b50f7ea -DSTRATA_DEVICE=vulkan
cmake --build backends/build-models --target strata-ggml --parallel 12
```

Use `cpu`, `vulkan` or `cuda`. Windows needs a developer environment with LLVM and the matching MSVC/Windows SDK.
Vulkan needs a local SDK with glslc/SPIRV-Headers; CUDA needs a Pascal-compatible CUDA12.9 toolchain and sm61.
CPU flags are explicit Ivy Bridge O3 without AVX2/FMA/F16C; MSVC CUDA host flags are O2/Ob3/Intel64/precise.
The source fetcher excludes weights and supports `--resume` only for its own identified source checkout.
No driver, global environment, power setting or system NUMA policy is changed.

## Prepare a local model profile

```sh
python backends/prepare-profile.py --model /local/model.gguf --engine /local/strata-ggml.exe --output /new/private/profile --backend vulkan --device Vulkan1 --context 131072
```

`Vulkan1` is only an example: verify that the selected device is the intended RX580. There is no automatic fallback
onto a working P40. CPU profiles need no device argument; CUDA uses an explicit `CUDA0`, `CUDA1`, etc.
The output is never overwritten and contains a private local API key with a local gitignore. Never publish it.
Port8080 and the current Qwen port8093 are rejected; the default prepared port is8094.
The tool prepares files only: it does not start an API, register autostart or replace the active model.
Run the full runtime/dependency/owner/model/hardware qualification before installing or activating a new instance.

Native MTP is required by default. A canonical compatible NextN block must be in the GGUF or supplied through
`--draft-model`; absent/incompatible heads fail explicitly. `--mtp off` is an explicit alternative, never a silent fallback.
GGML uses `--mtp-draft-tokens 2`; Poly uses `--window 3`; the existing Qwen engine keeps `--spec 3`.
Lookup, DSpark/DFlash and separate assistants are not called native MTP.
The optional profiles conservatively use model-compatible F16 caches; this does not change Qwen's128K/Q4 preset.
GPU profiles request memory fitting with a 1 GiB margin and keep the requested context minimum. A separate head
GGUF defaults to CPU so it cannot unexpectedly duplicate a large model on the GPU; its speed is not assumed.
Legacy DeepSeek V3 templates, DeepSeek V4.1/Engram and family-specific vision are not qualified by this profile builder.

## Separate V4.1 build experiment

The existing `strata-dsv41` source is compiled separately for CUDA12.9/sm61/Ivy Bridge. `dsv41-cuda-compat.cmake`
uses pinned build copies to guard unsupported descriptor/WMMA features and links Clang's CPU-detection builtins;
it retains the existing major>=7 tensor-core dispatch guards and Pascal F32 paths. Root source and the active
Qwen build are unchanged. This is compile/startup proof, not numerical/model qualification.
Its trained predictor is DSpark (`mtp.*` blocks). Do not describe it as native NextN or satisfy an explicit predictor
request with the engine's automatic off mode. Pack/Engram, predictor presence, no-pin and GPU checks are required
before a future activation; this optional engine remains OFF in production.

Sources and notices: [Strata](https://github.com/Niko1221/Strata), [Xolotl](https://github.com/Indras-Mirror/Xolotl),
[PolyStrata](https://github.com/VecSzn/PolyStrata), [Maya](https://github.com/mw00/project-maya),
[polaris-local-ai](https://github.com/AvilaCarlosDev/polaris-local-ai), and the pinned official GGML/llama.cpp library.
