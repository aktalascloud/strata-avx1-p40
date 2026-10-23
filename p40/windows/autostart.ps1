[CmdletBinding()]
param([switch]$CheckOnly,[switch]$Elevated,[string]$UserId=([Security.Principal.WindowsIdentity]::GetCurrent().Name))
$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot 'task-common.ps1')
$root=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..')).TrimEnd('\')
$identity=Get-PortableTaskIdentity $root
if($CheckOnly){
    [pscustomobject]@{startup_name=$identity.StartupName;control_name=$identity.ControlName;startup_xml=(Get-PortableTaskXml $root $UserId -Boot);control_xml=(Get-PortableTaskXml $root $UserId -Control);registered=$false}|ConvertTo-Json -Depth 4
    return
}
if(-not(Test-Path -LiteralPath (Join-Path $root 'strata-davidau.json'))){throw 'Run INSTALL.cmd first.'}
$principal=[Security.Principal.WindowsPrincipal]::new([Security.Principal.WindowsIdentity]::GetCurrent())
if(-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){
    if($Elevated){throw 'Administrator approval is required to register a boot task.'}
    $powershell=Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $arguments='-NoProfile -ExecutionPolicy Bypass -File "'+$PSCommandPath+'" -Elevated -UserId "'+$UserId+'"'
    Write-Output 'Windows administrator approval is required for boot-task registration. No password is stored.'
    $process=Start-Process -FilePath $powershell -ArgumentList $arguments -Verb RunAs -WindowStyle Hidden -Wait -PassThru
    if($process.ExitCode -ne 0){throw 'Boot-task registration was not completed; installation files were retained.'}
    return
}
$state=Join-Path $root 'runtime\task-registration.json'
try{
    foreach($control in @($true,$false)){
        $name=if($control){$identity.ControlName}else{$identity.StartupName}
        $task=Get-ScheduledTask -TaskPath '\' -TaskName $name -ErrorAction SilentlyContinue
        if($task){
            Assert-PortableTask $task $root $UserId -Control:$control
            if([string]$task.State -eq 'Running'){throw 'Stop this installation gracefully before changing its startup tasks.'}
        }
        $xml=Get-PortableTaskXml $root $UserId -Control:$control -Boot:(-not $control)
        Register-ScheduledTask -TaskPath '\' -TaskName $name -Xml $xml -Force|Out-Null
        $actual=Get-ScheduledTask -TaskPath '\' -TaskName $name -ErrorAction Stop
        Assert-PortableTask $actual $root $UserId -Control:$control -RequireBoot:(-not $control)
    }
    $result=@{status='enabled';root=$root;startup_name=$identity.StartupName;control_name=$identity.ControlName;user_id=$UserId;utc=[DateTime]::UtcNow.ToString('o');boot_delay_seconds=45;requires_codex=$false;requires_interactive_logon=$false}
    [IO.File]::WriteAllText($state,($result|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
    Write-Output 'Boot tasks verified. They run independently of Codex and do not require interactive logon. No reboot was performed.'
}catch{
    [IO.File]::WriteAllText($state,(@{status='failed';error=$_.Exception.Message;utc=[DateTime]::UtcNow.ToString('o')}|ConvertTo-Json),[Text.UTF8Encoding]::new($false))
    throw
}
