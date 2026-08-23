param([string]$TaskName = "AutonomousSpotAgent-Stage2")

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"
$configPath = Join-Path $projectRoot "config.stage2-live.toml"
if (-not (Test-Path -LiteralPath $pythonPath)) { throw "Install the project first: $pythonPath" }
$arguments = "-m spot_agent run-once --config `"$configPath`" --execute"
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument $arguments -WorkingDirectory $projectRoot
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) `
    -RepetitionInterval (New-TimeSpan -Hours 4)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings `
    -Description "Low-frequency BTCUSDT Spot agent; same-user Windows Credential Manager required"
Write-Output "Registered $TaskName. Inspect it in Windows Task Scheduler before enabling live capital."

