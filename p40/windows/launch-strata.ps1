[CmdletBinding()]
param([switch]$CheckOnly,[switch]$Worker)
$ErrorActionPreference='Stop'
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
if($settings.host -ne '127.0.0.1' -or $settings.port -ne 8093 -or $settings.vision.gpu -ne $false){throw 'Expected localhost8093 and CPU-only vision.'}
$hash=[Security.Cryptography.SHA256]::Create()
try{$id=([BitConverter]::ToString($hash.ComputeHash([Text.Encoding]::UTF8.GetBytes($root.ToLowerInvariant())))).Replace('-','').Substring(0,8)}finally{$hash.Dispose()}
$taskName='Strata AVX1 P40 - '+$id
$powershell=Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
$arguments='-NoProfile -ExecutionPolicy Bypass -File "'+$PSCommandPath+'" -Worker'
if(-not $Worker){
    $listener=@(Get-NetTCPConnection -State Listen -LocalPort 8093 -ErrorAction SilentlyContinue)
    if($listener.Count){throw 'Port8093 is occupied. Existing services were not stopped or changed.'}
    $task=Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if($task){
        if($task.Actions.Count -ne 1 -or $task.Actions[0].Execute -ne $powershell -or $task.Actions[0].Arguments -ne $arguments -or $task.Actions[0].WorkingDirectory -ne $root){throw 'Existing task does not match this installation.'}
    }else{
        $user=[Security.Principal.WindowsIdentity]::GetCurrent().Name
        $action=New-ScheduledTaskAction -Execute $powershell -Argument $arguments -WorkingDirectory $root
        $principal=New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
        $taskSettings=New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
        Register-ScheduledTask -TaskName $taskName -Action $action -Principal $principal -Settings $taskSettings -Description 'Portable Strata AVX1/P40; manual task, independent of the initiating terminal.'|Out-Null
    }
    Start-ScheduledTask -TaskName $taskName
    Write-Output "Started independent Windows task: $taskName"
    Write-Output 'Loading weights may take several minutes. Open http://127.0.0.1:8093/ after /health reports loaded:true. STOP.cmd performs graceful drain.'
    return
}
$self=Get-CimInstance Win32_Process -Filter ("ProcessId="+$PID)
$parent=Get-CimInstance Win32_Process -Filter ("ProcessId="+$self.ParentProcessId)
if($parent.Name -notin @('taskeng.exe','taskhostw.exe','svchost.exe') -or $parent.ExecutablePath -notlike "$env:WINDIR\System32\*"){throw 'Worker may run only through Windows Task Scheduler.'}
$lock=[IO.File]::Open((Join-Path $root 'launch.lock'),[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
try{
    $probe=[Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback,8093)
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
    $state=@{schema=3;pid=$p.Id;python=$python;config=$config;base_config=$config;source=(Join-Path $root 'app');engine=$settings.exe;vision=$settings.vision.exe;version=$active.id;started_utc=$p.StartTime.ToUniversalTime().ToString('o');launcher=@{broker='PortableWindowsTaskScheduler';task_name=$taskName;pid=$PID};control=@{protocol='local_file_drain_v1';path=$controlPath;nonce=$nonce;bootstrap_sha256=(Get-FileHash -LiteralPath $bootstrap).Hash;review_sha256=(Get-FileHash -LiteralPath $review).Hash}}
    [IO.File]::WriteAllText((Join-Path $root 'strata-server-launch.json'),($state|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
    $p.WaitForExit();exit $p.ExitCode
}finally{$lock.Dispose()}
