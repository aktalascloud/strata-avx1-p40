[CmdletBinding()]
param([switch]$CheckOnly)
$ErrorActionPreference='Stop'
if(-not [Environment]::Is64BitOperatingSystem){throw 'Windows x64 is required.'}
if(-not(Test-Path -LiteralPath (Join-Path $env:WINDIR 'System32\nvcuda.dll'))){throw 'Install a P40-compatible NVIDIA driver supporting CUDA12.9 first. This package never installs or changes GPU drivers.'}
$runtime=Join-Path $env:WINDIR 'System32\msvcp140.dll'
$needed=-not(Test-Path -LiteralPath $runtime)
if(-not $needed){
    $v=(Get-Item -LiteralPath $runtime).VersionInfo
    $needed=$v.FileMajorPart -lt 14 -or ($v.FileMajorPart -eq 14 -and $v.FileMinorPart -lt 44)
}
if(-not $needed){Write-Output 'Microsoft Visual C++ runtime is available.';return}
if($CheckOnly){throw 'Install Microsoft Visual C++ v14 x64: https://aka.ms/vs/17/release/vc_redist.x64.exe'}
$root=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$downloads=Join-Path $root 'downloads';[IO.Directory]::CreateDirectory($downloads)|Out-Null
$installer=Join-Path $downloads 'vc_redist.x64.exe'
Write-Output 'Downloading the Microsoft runtime directly from Microsoft. Review its license in the installer.'
[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
Invoke-WebRequest -UseBasicParsing -Uri 'https://aka.ms/vs/17/release/vc_redist.x64.exe' -OutFile $installer
$signature=Get-AuthenticodeSignature -LiteralPath $installer
if($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'O=Microsoft Corporation'){throw 'Microsoft installer signature validation failed.'}
$p=Start-Process -FilePath $installer -ArgumentList @('/install','/norestart') -Wait -PassThru
if($p.ExitCode -notin @(0,1638,3010)){throw "Microsoft runtime installer failed: $($p.ExitCode)"}
if($p.ExitCode -eq 3010){Write-Output 'Microsoft reports that a restart is required. Restart manually; this script never reboots Windows.'}
