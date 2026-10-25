param([ValidateSet('cpu','vulkan','cuda')][string]$Backend='cpu',[ValidateRange(1,12)][int]$Workers=12,[string]$VulkanRoot='',
 [ValidateSet('production','models')][string]$Library='models',[string[]]$Targets=@('strata-ggml','strata-security-check','strata-numerical-check'))
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
. (Join-Path $root 'tools/portable-env.ps1')
$e=Set-StrataBuildEnvironment $root
. (Join-Path $root 'tools/compiler-profile.ps1')
$p=Get-StrataCompilerProfile $root ''
if($Library -eq 'models'){
 $review=Get-Content (Join-Path $PSScriptRoot 'model-library-review.json') -Raw|ConvertFrom-Json
 if(-not $review.semantic_reviewed_for_experimental_build){throw 'Model library semantic review required'}
 $source=Join-Path $root 'deps/llama-models-b9acf138';$pin=[string]$review.source_sha
 $actual=(& $e.git -C $source rev-parse HEAD).Trim()
 if($LASTEXITCODE -or $actual -ne $pin){throw 'Model library source pin mismatch'}
 $dirty=@(& $e.git -C $source status --porcelain)
 if($LASTEXITCODE -or $dirty.Count){throw 'Model library must be an unchanged pinned checkout'}
}else{
 & (Join-Path $root 'runtime/python/python.exe') (Join-Path $PSScriptRoot 'verify-dependency.py')
 if($LASTEXITCODE){throw 'Embedded library dependency pin mismatch'}
 $source=Join-Path $root 'deps/llama.cpp';$pin='3cf03257f219afbe7334045ff7c6a06ac68c627d'
}
if($Backend -eq 'vulkan'){
 if(-not $VulkanRoot -or -not(Test-Path -LiteralPath (Join-Path $VulkanRoot 'Bin/glslc.exe'))){throw 'Private Vulkan SDK with glslc is required; no driver or global SDK is installed automatically'}
 $env:VULKAN_SDK=[IO.Path]::GetFullPath($VulkanRoot)
}
$suffix=if($Library -eq 'models'){'-models'}else{''}
$b=Join-Path $root "work/build-ggml-$Backend-ivy$suffix"
$a=@('-S',"$PSScriptRoot/ggml",'-B',$b,'-G','Ninja','-DCMAKE_BUILD_TYPE=Release',
 "-DCMAKE_MAKE_PROGRAM=$($e.ninja)","-DCMAKE_C_COMPILER=$($p.cpu_compiler)","-DCMAKE_CXX_COMPILER=$($p.cpu_compiler)",
 "-DCMAKE_LINKER=$($e.vcbin)/link.exe",('-DCMAKE_C_FLAGS_RELEASE='+$p.cpu_release_flags),('-DCMAKE_CXX_FLAGS_RELEASE='+$p.cpu_release_flags),
 "-DSTRATA_LLAMA_SOURCE=$source","-DSTRATA_LLAMA_PIN=$pin","-DSTRATA_DEVICE=$Backend","-DSTRATA_PRIVATE_PYTHON=$root/runtime/python/python.exe",'-DGGML_CCACHE=OFF',
 '-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON')
if($Backend -eq 'cuda'){
 $a+=@("-DCMAKE_CUDA_HOST_COMPILER=$($e.vcbin)/cl.exe","-DCMAKE_CUDA_COMPILER=$($e.cuda)/bin/nvcc.exe", "-DCUDAToolkit_ROOT=$($e.cuda)",
 '-DCMAKE_CUDA_ARCHITECTURES=61','-DCMAKE_CUDA_FLAGS=--allow-unsupported-compiler -Xcompiler=/arch:AVX',('-DCMAKE_CUDA_FLAGS_RELEASE='+$p.cuda_release_flags))
}
& $e.cmake @a
if($LASTEXITCODE){throw 'Embedded backend configure failed'}
& $e.cmake --build $b --target @Targets --parallel $Workers
if($LASTEXITCODE){throw 'Embedded backend build failed'}
