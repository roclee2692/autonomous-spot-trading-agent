param([switch]$Execute)

$ErrorActionPreference = "Stop"
$pythonPath = Join-Path $PSScriptRoot "..\.venv\Scripts\python.exe"
$configPath = Join-Path $PSScriptRoot "..\config.stage2-live.toml"
$arguments = @("-m", "spot_agent", "run-once", "--config", $configPath)
if ($Execute) { $arguments += "--execute" }
& $pythonPath @arguments

