$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '..\windows\task-common.ps1')
$testRoot=Join-Path $env:TEMP 'Strata & portable test'
$user=[Security.Principal.WindowsIdentity]::GetCurrent().Name
$identity=Get-PortableTaskIdentity $testRoot
if($identity.StartupName -eq (Get-PortableTaskIdentity ($testRoot+'-other')).StartupName){throw 'Distinct folders share a task name.'}
[xml]$xml=Get-PortableTaskXml $testRoot $user -Boot
$ns=[Xml.XmlNamespaceManager]::new($xml.NameTable);$ns.AddNamespace('t',$xml.DocumentElement.NamespaceURI)
$exec=$xml.SelectSingleNode('//t:Exec',$ns)
if($exec.WorkingDirectory -ne $testRoot -or $exec.Arguments -notlike ('*"'+$testRoot+'\p40\windows\launch-strata.ps1" -Worker')){throw 'Task paths were not quoted or XML escaped correctly.'}
$task=[pscustomobject]@{
    Description=('STRATA_PUBLIC_START_V2:'+$identity.Id)
    Actions=@([pscustomobject]@{Execute=[string]$exec.Command;Arguments=[string]$exec.Arguments;WorkingDirectory=$testRoot})
    Principal=[pscustomobject]@{UserId=$user;LogonType='S4U';RunLevel='Limited'}
    Settings=[pscustomobject]@{AllowHardTerminate=$false;ExecutionTimeLimit='PT0S';MultipleInstances='IgnoreNew'}
    Triggers=@([pscustomobject]@{CimClass=[pscustomobject]@{CimClassName='MSFT_TaskBootTrigger'};Enabled=$true;Delay='PT45S'})
}
Assert-PortableTask $task $testRoot $user -RequireBoot
$checks=2
foreach($mutation in @('wrong-path','hard-terminate','missing-trigger','wrong-description')){
    $copy=$task|ConvertTo-Json -Depth 8|ConvertFrom-Json
    switch($mutation){
        'wrong-path'{$copy.Actions[0].WorkingDirectory=$testRoot+'-other'}
        'hard-terminate'{$copy.Settings.AllowHardTerminate=$true}
        'missing-trigger'{$copy.Triggers=@()}
        'wrong-description'{$copy.Description='unmanaged task'}
    }
    $rejected=$false
    try{Assert-PortableTask $copy $testRoot $user -RequireBoot}catch{$rejected=$true}
    if(-not $rejected){throw "Task guard accepted $mutation"};$checks++
}
Write-Output "Portable task tests passed: $checks. No task was registered or started."
