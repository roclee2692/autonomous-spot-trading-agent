param([string]$VenvPath = ".venv")

$ErrorActionPreference = "Stop"
python -m venv $VenvPath
$pythonPath = Join-Path $VenvPath "Scripts\python.exe"
& $pythonPath -m pip install --upgrade pip
& $pythonPath -m pip install -e .
Write-Output "Installed. Run: $pythonPath -m spot_agent --help"

