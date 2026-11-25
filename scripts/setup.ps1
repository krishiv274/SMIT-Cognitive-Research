# One-time setup on Windows (PowerShell): requires Python 3.11+ and Node.js 20+ on PATH.
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
if (-not (Test-Path ".venv")) { py -3 -m venv .venv }
& ".venv\Scripts\python.exe" -m pip install --upgrade pip
& ".venv\Scripts\pip.exe" install -r backend\requirements-dev.txt
Push-Location frontend; npm ci; npm run build; Pop-Location
if (-not (Test-Path ".env")) { Copy-Item .env.example .env; Write-Host "Created .env - EDIT passwords/secrets before real data collection." }
Write-Host "Setup complete. Start with: .\scripts\start.ps1"
