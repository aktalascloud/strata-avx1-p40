param([ValidateRange(1,12)][int]$Workers=12,[switch]$ConfigureOnly,[string[]]$Targets=@('strata-poly','poly_workers_test','poly_guesses_test','poly_conversations_test'),[switch]$Dsv41)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
. (Join-Path $root 'tools/portable-env.ps1')
$e=Set-StrataBuildEnvironment $root
. (Join-Path $root 'tools/compiler-profile.ps1')
$p=Get-StrataCompilerProfile $root ''
& (Join-Path $root 'runtime/python/python.exe') (Join-Path $PSScriptRoot 'verify-sources.py')
if($LASTEXITCODE){throw 'Optional backend source proof failed'}
$b=Join-Path $root $(if($Dsv41){'work/build-dsv41-sm61-ivy'}else{'work/build-poly-sm61-ivy-core'})
$args=@('-S',"$root/upstream",'-B',$b,'-G','Ninja','-DCMAKE_BUILD_TYPE=Release',"-DCMAKE_MAKE_PROGRAM=$($e.ninja)",
 "-DSTRATA_BACKENDS_DIR=$PSScriptRoot","-DCMAKE_PROJECT_strata_INCLUDE=$PSScriptRoot/inject.cmake",
 "-DSTRATA_CORE_SOURCE=$root/upstream","-DCMAKE_C_COMPILER=$($p.cpu_compiler)","-DCMAKE_CXX_COMPILER=$($p.cpu_compiler)",
 "-DCMAKE_LINKER=$($e.vcbin)/link.exe","-DCMAKE_CUDA_HOST_COMPILER=$($e.vcbin)/cl.exe","-DCMAKE_CUDA_COMPILER=$($e.cuda)/bin/nvcc.exe",
 "-DCUDAToolkit_ROOT=$($e.cuda)",'-DCMAKE_CUDA_ARCHITECTURES=61',('-DCMAKE_C_FLAGS_RELEASE='+$p.cpu_release_flags),
 ('-DCMAKE_CXX_FLAGS_RELEASE='+$p.cpu_release_flags),'-DCMAKE_CUDA_FLAGS=--allow-unsupported-compiler -Xcompiler=/arch:AVX',
 ('-DCMAKE_CUDA_FLAGS_RELEASE='+$p.cuda_release_flags),'-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON',
 '-DSTRATA_ENABLE_CUDA=ON','-DSTRATA_ENABLE_HIP=OFF','-DSTRATA_ENABLE_SYCL=OFF','-DSTRATA_EXPERIMENTAL_SM60=ON',
 '-DSTRATA_ISA_FLOOR=avx','-DSTRATA_PORTABLE=OFF','-DSTRATA_NATIVE_EXPERTS=ON','-DSTRATA_Q6K_EXPERTS=ON',
 '-DSTRATA_MMQ_KQUANTS=ON','-DSTRATA_IVYBRIDGE_O3=ON','-DSTRATA_PASCALLAMA=ON',
 ("-DSTRATA_PASCALLAMA_PATCH="+$p.pascallama_patch),"-DSTRATA_PRIVATE_GIT=$($e.git)",
 "-DSTRATA_GGML_DIR=$root/deps/llama.cpp",'-DSTRATA_BUILD_TESTS=OFF','-DGGML_CCACHE=OFF')
if($Dsv41){$args+='-DSTRATA_BUILD_DSV41=ON'}
& $e.cmake @args
if($LASTEXITCODE){throw 'Optional backend configure failed'}
. (Join-Path $root 'tools/mmq-tile-profile.ps1')
Set-StrataMmqTileProfile $root $b ([int]$p.pascal_mmq_i)|Out-Null
if(-not $ConfigureOnly){
 & $e.cmake --build $b --target @Targets --parallel $Workers
 if($LASTEXITCODE){throw 'Optional backend build failed'}
}
