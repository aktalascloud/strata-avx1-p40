$ErrorActionPreference='Stop'
function Get-PortableTaskIdentity {
    param([string]$Root)
    $canonical=[IO.Path]::GetFullPath($Root).TrimEnd('\')
    $sha=[Security.Cryptography.SHA256]::Create()
    try{$id=([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($canonical.ToLowerInvariant())))).Replace('-','').Substring(0,8)}finally{$sha.Dispose()}
    return @{Root=$canonical;Id=$id;StartupName=('Strata AVX1 P40 - '+$id);ControlName=('Strata AVX1 P40 control - '+$id)}
}
function Get-PortableTaskXml {
    param([string]$Root,[string]$UserId,[switch]$Control,[switch]$Boot)
    $identity=Get-PortableTaskIdentity $Root
    $escape={param($text)[Security.SecurityElement]::Escape([string]$text)}
    $user=&$escape $UserId;$working=&$escape $identity.Root
    $kind=if($Control){'CONTROL'}else{'START'}
    $description='STRATA_PUBLIC_'+$kind+'_V2:'+ $identity.Id
    $logon=if($Boot -or $Control){'S4U'}else{'InteractiveToken'}
    $triggers=if($Boot -and -not $Control){'<BootTrigger><Enabled>true</Enabled><Delay>PT45S</Delay></BootTrigger>'}else{''}
    if($Control){
        $exe=&$escape (Join-Path $identity.Root 'runtime\python\python.exe')
        $arguments=&$escape ('-I -s -B "'+(Join-Path $identity.Root 'tools\scheduler_control.py')+'"')
    }else{
        $exe=&$escape (Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe')
        $arguments=&$escape ('-NoProfile -ExecutionPolicy Bypass -File "'+(Join-Path $identity.Root 'p40\windows\launch-strata.ps1')+'" -Worker')
    }
    return @"
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
 <RegistrationInfo><Description>$description</Description></RegistrationInfo>
 <Triggers>$triggers</Triggers>
 <Principals><Principal id="Owner"><UserId>$user</UserId><LogonType>$logon</LogonType><RunLevel>LeastPrivilege</RunLevel></Principal></Principals>
 <Settings><MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy><DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries><StopIfGoingOnBatteries>false</StopIfGoingOnBatteries><AllowHardTerminate>false</AllowHardTerminate><StartWhenAvailable>true</StartWhenAvailable><RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable><RunOnlyIfIdle>false</RunOnlyIfIdle><IdleSettings><StopOnIdleEnd>false</StopOnIdleEnd><RestartOnIdle>false</RestartOnIdle></IdleSettings><Enabled>true</Enabled><ExecutionTimeLimit>PT0S</ExecutionTimeLimit><Priority>4</Priority></Settings>
 <Actions Context="Owner"><Exec><Command>$exe</Command><Arguments>$arguments</Arguments><WorkingDirectory>$working</WorkingDirectory></Exec></Actions>
</Task>
"@
}
function Assert-PortableTask {
    param($Task,[string]$Root,[string]$UserId,[switch]$Control,[switch]$RequireBoot)
    $identity=Get-PortableTaskIdentity $Root
    $kind=if($Control){'CONTROL'}else{'START'}
    $description='STRATA_PUBLIC_'+$kind+'_V2:'+ $identity.Id
    if(-not $Task -or $Task.Description -ne $description){throw 'Task identity differs from this installation.'}
    [xml]$expected=Get-PortableTaskXml $Root $UserId -Control:$Control -Boot:$RequireBoot
    $ns=[Xml.XmlNamespaceManager]::new($expected.NameTable);$ns.AddNamespace('t',$expected.DocumentElement.NamespaceURI)
    $exec=$expected.SelectSingleNode('//t:Exec',$ns)
    if($Task.Actions.Count -ne 1 -or $Task.Actions[0].Execute -ne $exec.Command -or $Task.Actions[0].Arguments -ne $exec.Arguments -or $Task.Actions[0].WorkingDirectory -ne $identity.Root){throw 'Task action differs from this installation.'}
    $sid=if($Task.Principal.UserId -like 'S-1-*'){$Task.Principal.UserId}else{([Security.Principal.NTAccount]$Task.Principal.UserId).Translate([Security.Principal.SecurityIdentifier]).Value}
    $wantedSid=([Security.Principal.NTAccount]$UserId).Translate([Security.Principal.SecurityIdentifier]).Value
    if($sid -ne $wantedSid -or $Task.Principal.RunLevel -ne 'Limited'){throw 'Task owner or privilege level differs.'}
    if($Task.Settings.AllowHardTerminate -or $Task.Settings.ExecutionTimeLimit -ne 'PT0S' -or $Task.Settings.MultipleInstances -ne 'IgnoreNew'){throw 'Task lifetime policy differs.'}
    $triggers=@($Task.Triggers|Where-Object {$_})
    if($Control){
        if($Task.Principal.LogonType -ne 'S4U' -or $triggers.Count -ne 0){throw 'Control task must use S4U without triggers.'}
    }elseif($RequireBoot -or $Task.Principal.LogonType -eq 'S4U'){
        if($Task.Principal.LogonType -ne 'S4U' -or $triggers.Count -ne 1 -or $triggers[0].CimClass.CimClassName -ne 'MSFT_TaskBootTrigger' -or -not $triggers[0].Enabled -or $triggers[0].Delay -ne 'PT45S'){throw 'Boot task trigger or logon policy differs.'}
    }elseif($Task.Principal.LogonType -ne 'Interactive' -or $triggers.Count -ne 0){throw 'Manual task policy differs.'}
}
