[CmdletBinding()]
param([switch]$CheckOnly,[switch]$Worker)
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'task-common.ps1')
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..')).TrimEnd('\')
$python=Join-Path $root 'runtime\python\python.exe'
$config=Join-Path $root 'strata-davidau.json'
if($CheckOnly){
    & $python -I -s -B (Join-Path $PSScriptRoot 'installer.py') --check-bundle
    if($LASTEXITCODE -ne 0){throw 'Bundle validation failed.'}
    Write-Output 'No task registered, server started or model downloaded.';return
}
if(-not(Test-Path -LiteralPath $config)){throw 'Run INSTALL.cmd first.'}
$settings=Get-Content -LiteralPath $config -Raw|ConvertFrom-Json
$prefix=$root+'\'
foreach($value in @($settings.exe,$settings.cwd,$settings.tokenizer,$settings.vision.exe)){
    if(-not [IO.Path]::GetFullPath($value).StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)){throw 'Executable/source/tokenizer paths must stay in this installation. Reinstall the preset after moving it.'}
    if(-not(Test-Path -LiteralPath $value)){throw "Required path is missing: $value"}
}
if($settings.host -ne '127.0.0.1' -or $settings.port -isnot [int] -or $settings.port -lt 1024 -or $settings.port -gt 65535 -or $settings.vision.gpu -ne $false){throw 'Expected a valid localhost port and CPU-only vision.'}
$port=[int]$settings.port
$identity=Get-PortableTaskIdentity $root
$taskName=$identity.StartupName
$powershell=Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
$arguments='-NoProfile -ExecutionPolicy Bypass -File "'+$PSCommandPath+'" -Worker'
if(-not $Worker){
    $listener=@(Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue)
    if($listener.Count){throw "Port $port is occupied. Existing services were not stopped or changed."}
    $task=Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    $user=[Security.Principal.WindowsIdentity]::GetCurrent().Name
    if($task){
        Assert-PortableTask $task $root $user
    }else{
        $xml=Get-PortableTaskXml $root $user
        Register-ScheduledTask -TaskPath '\' -TaskName $taskName -Xml $xml|Out-Null
        Assert-PortableTask (Get-ScheduledTask -TaskPath '\' -TaskName $taskName) $root $user
    }
    Start-ScheduledTask -TaskName $taskName
    Write-Output "Started independent Windows task: $taskName"
    Write-Output "Loading weights may take several minutes. Open http://127.0.0.1:$port/ after /health reports loaded:true. STOP.cmd performs graceful drain."
    return
}
& $python -I -s -B (Join-Path $root 'tools\scheduler_control.py') --check-context
if($LASTEXITCODE -ne 0){throw 'Worker may run only through Windows Task Scheduler.'}
$lock=[IO.File]::Open((Join-Path $root 'launch.lock'),[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
try{
    $probe=[Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback,$port)
    try{$probe.Start()}finally{$probe.Stop()}
    $logs=Join-Path $root 'logs';$stateDir=Join-Path $root 'runtime\state'
    [IO.Directory]::CreateDirectory($logs)|Out-Null;[IO.Directory]::CreateDirectory($stateDir)|Out-Null
    $rng=[Security.Cryptography.RandomNumberGenerator]::Create();$bytes=New-Object byte[] 32
    try{$rng.GetBytes($bytes)}finally{$rng.Dispose()}
    $nonce=([BitConverter]::ToString($bytes)).Replace('-','').ToLowerInvariant()
    $controlPath=Join-Path $stateDir ('control-'+$nonce+'.json')
    $bootstrap=Join-Path $root 'tools\start-server.py'
    $review=Join-Path $root 'tools\service-control-review.json'
    function Quote-Argument([string]$value){
        if($value.Length -and $value -notmatch '[\s"]'){return $value}
        $out='"';$slashes=0
        foreach($c in $value.ToCharArray()){
            if($c -eq '\'){$slashes++;continue}
            if($c -eq '"'){$out+=('\'*(2*$slashes+1))+'"'}else{$out+=('\'*$slashes)+$c};$slashes=0
        }
        return $out+('\'*(2*$slashes))+'"'
    }
    $argv=@('-I','-s','-B','-u',$bootstrap,'--source',(Join-Path $root 'app'),'--config',$config,'--control-path',$controlPath,'--control-nonce',$nonce)
    $command=($argv|ForEach-Object{Quote-Argument $_}) -join ' '
    $p=Start-Process -FilePath $python -ArgumentList $command -WorkingDirectory (Join-Path $root 'app') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logs 'server.stdout.log') -RedirectStandardError (Join-Path $logs 'server.stderr.log')
    $active=Get-Content -LiteralPath (Join-Path $root 'runtime\active.json') -Raw|ConvertFrom-Json
    $state=@{schema=3;pid=$p.Id;python=$python;config=$config;base_config=$config;source=(Join-Path $root 'app');engine=$settings.exe;vision=$settings.vision.exe;version=$active.id;started_utc=$p.StartTime.ToUniversalTime().ToString('o');launcher=@{broker='PortableWindowsTaskScheduler';task_name=$taskName;control_task_name=$identity.ControlName;logon_type=[string](Get-ScheduledTask -TaskPath '\' -TaskName $taskName).Principal.LogonType;pid=$PID};control=@{protocol='local_file_drain_v1';path=$controlPath;nonce=$nonce;bootstrap_sha256=(Get-FileHash -LiteralPath $bootstrap).Hash;review_sha256=(Get-FileHash -LiteralPath $review).Hash}}
    [IO.File]::WriteAllText((Join-Path $root 'strata-server-launch.json'),($state|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
    $p.WaitForExit();exit $p.ExitCode
}finally{$lock.Dispose()}
