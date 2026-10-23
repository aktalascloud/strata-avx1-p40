[CmdletBinding()]
param([string]$Clang='clang-cl.exe',[string]$Cuda=$env:CUDA_PATH,[int]$Jobs=12)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$profile=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'build-profile.json') -Raw|ConvertFrom-Json
$pins=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'patches\manifest.json') -Raw|ConvertFrom-Json
foreach($command in @('cmake','ninja','git','cl.exe',$Clang)){if(-not(Get-Command $command -ErrorAction SilentlyContinue)){throw "Missing prerequisite: $command. Use a VS2022 x64 Developer PowerShell with Clang and CUDA12.9."}}
if(-not $Cuda){throw 'CUDA_PATH or -Cuda is required.'}
$nvcc=Join-Path $Cuda 'bin\nvcc.exe'
if((& $nvcc -V|Out-String) -notmatch 'release 12\.9'){throw 'This profile is qualified with CUDA12.9 only.'}
if($Jobs -lt 1 -or $Jobs -gt 256){throw 'Invalid parallelism'}
$env:GIT_CONFIG_NOSYSTEM='1';$env:GIT_CONFIG_GLOBAL='NUL'
$env:STRATA_NO_CPU_PIN='1';$env:NVCC_PREPEND_FLAGS='--use-local-env'
$env:CMAKE_BUILD_PARALLEL_LEVEL=[string]$Jobs
$git=(Get-Command git).Source;$hostCompiler=(Get-Command cl.exe).Source;$compiler=(Get-Command $Clang).Source
foreach($entry in $pins.patches){if((Get-FileHash -LiteralPath (Join-Path $root $entry.path)).Hash.ToLowerInvariant() -ne $entry.sha256){throw 'Reviewed patch bytes changed.'}}
$deps=Join-Path $root '.p40-deps\llama.cpp'
if(-not(Test-Path -LiteralPath $deps)){
    & $git -c core.autocrlf=false clone --filter=blob:none --no-checkout https://github.com/ggml-org/llama.cpp.git $deps
    if($LASTEXITCODE -ne 0){throw 'Dependency clone failed'}
}
& $git -C $deps fetch --depth=1 origin $pins.ggml_sha
if($LASTEXITCODE -ne 0){throw 'Pinned GGML fetch failed'}
& $git -C $deps checkout --detach $pins.ggml_sha
if($LASTEXITCODE -ne 0){throw 'Pinned GGML checkout failed'}
$build=Join-Path $root ('work\p40-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[Guid]::NewGuid().ToString('N').Substring(0,8))
$args=@('-S',$root,'-B',$build,'-G','Ninja','-DCMAKE_BUILD_TYPE=Release',
    "-DCMAKE_C_COMPILER=$compiler","-DCMAKE_CXX_COMPILER=$compiler",'-DCMAKE_LINKER=link.exe',
    "-DCMAKE_CUDA_HOST_COMPILER=$hostCompiler","-DCMAKE_CUDA_COMPILER=$nvcc","-DCUDAToolkit_ROOT=$Cuda",
    '-DCMAKE_CUDA_ARCHITECTURES=61',('-DCMAKE_C_FLAGS_RELEASE='+$profile.cpu_release_flags),('-DCMAKE_CXX_FLAGS_RELEASE='+$profile.cpu_release_flags),
    '-DCMAKE_CUDA_FLAGS=--allow-unsupported-compiler -Xcompiler=/arch:AVX',('-DCMAKE_CUDA_FLAGS_RELEASE='+$profile.cuda_release_flags),
    '-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON',
    '-DSTRATA_ENABLE_CUDA=ON','-DSTRATA_ENABLE_HIP=OFF','-DSTRATA_ENABLE_SYCL=OFF','-DSTRATA_EXPERIMENTAL_SM60=ON',
    '-DSTRATA_ISA_FLOOR=avx','-DSTRATA_PORTABLE=OFF','-DSTRATA_NATIVE_EXPERTS=ON','-DSTRATA_Q6K_EXPERTS=ON',
    '-DSTRATA_MMQ_KQUANTS=ON','-DSTRATA_IVYBRIDGE_O3=ON','-DSTRATA_PASCALLAMA=ON',
    ('-DSTRATA_PASCALLAMA_PATCH='+(Join-Path $PSScriptRoot 'patches\pascallama-sm61.patch')),
    "-DSTRATA_PRIVATE_GIT=$git","-DSTRATA_GGML_DIR=$deps",'-DSTRATA_BUILD_TESTS=ON','-DGGML_CCACHE=OFF')
& cmake @args
if($LASTEXITCODE -ne 0){throw 'Configure failed'}
& cmake --build $build --target strata strata_kq --parallel $Jobs
if($LASTEXITCODE -ne 0){throw 'Build failed'}
Write-Output "Engine built in $build. This is not a deployed or GPU-qualified release. Run the full numerical policy before using new bytes."
