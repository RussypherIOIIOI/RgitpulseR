param([ValidateSet('Enable', 'Disable', 'Status')][string]$Action = 'Status')
$ErrorActionPreference = 'Stop'
$gitpulseTaskName = 'GitPulse-Daily-Import'
if ($Action -eq 'Status') {
    Get-ScheduledTask -TaskName $gitpulseTaskName -ErrorAction Stop | Select-Object TaskName, State
    exit
}
if ($Action -eq 'Disable') {
    Disable-ScheduledTask -TaskName $gitpulseTaskName -ErrorAction Stop | Out-Null
    exit
}
if ((Get-TimeZone).Id -ne 'Mountain Standard Time') {
    throw 'The daily schedule requires Windows Mountain Standard Time (America/Denver); inspect timezone before enabling.'
}
$gitpulseRoot = Split-Path -Parent $PSScriptRoot
$gitpulseScript = Join-Path $PSScriptRoot 'daily-import.ps1'
$gitpulseShell = (Get-Command pwsh.exe -ErrorAction Stop).Source
$gitpulseAction = New-ScheduledTaskAction -Execute $gitpulseShell -Argument "-NoProfile -File `"$gitpulseScript`"" -WorkingDirectory $gitpulseRoot
$gitpulseTrigger = New-ScheduledTaskTrigger -Daily -At '09:00'
$gitpulseSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -RestartCount 2 -RestartInterval (New-TimeSpan -Minutes 5) -ExecutionTimeLimit (New-TimeSpan -Minutes 5)
if (Get-ScheduledTask -TaskName $gitpulseTaskName -ErrorAction SilentlyContinue) {
    Enable-ScheduledTask -TaskName $gitpulseTaskName | Out-Null
}
else {
    Register-ScheduledTask -TaskName $gitpulseTaskName -Action $gitpulseAction -Trigger $gitpulseTrigger -Settings $gitpulseSettings -Description 'Daily GitPulse batch through the same CLI, database lock and publication transaction.' | Out-Null
}
