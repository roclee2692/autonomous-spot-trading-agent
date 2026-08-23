param([string]$TaskName = "AutonomousSpotAgent-Stage2")

$ErrorActionPreference = "Stop"
Unregister-ScheduledTask -TaskName $TaskName -Confirm

