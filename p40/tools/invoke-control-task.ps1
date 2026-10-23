$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
. (Join-Path $root 'p40\windows\task-common.ps1')
$identity=Get-PortableTaskIdentity $root
$task=Get-ScheduledTask -TaskPath '\' -TaskName $identity.ControlName -ErrorAction Stop
$user=[Security.Principal.WindowsIdentity]::GetCurrent().Name
Assert-PortableTask $task $root $user -Control
if(-not $task.Settings.Enabled){throw 'The control task is disabled; no action.'}
$deadline=[DateTime]::UtcNow.AddSeconds(10)
while([string]$task.State -eq 'Running'){
    if([DateTime]::UtcNow -ge $deadline){throw 'Lifecycle task is already running; no duplicate action.'}
    Start-Sleep -Milliseconds 250
    $task=Get-ScheduledTask -TaskPath '\' -TaskName $identity.ControlName -ErrorAction Stop
}
Start-ScheduledTask -TaskPath '\' -TaskName $identity.ControlName -ErrorAction Stop
