# Start SMIT on Windows (PowerShell). Run scripts\setup.ps1 first.
$Root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path "$Root\frontend\dist")) { Push-Location "$Root\frontend"; npm run build; Pop-Location }
Set-Location "$Root\backend"
Write-Host "SMIT running at http://127.0.0.1:8000  (participant: /participate  researcher: /researcher)"
& "$Root\.venv\Scripts\uvicorn.exe" app.main:app --host 127.0.0.1 --port 8000
