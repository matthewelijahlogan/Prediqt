param([int]$Port = 8000, [switch]$NoBrowser)

$ErrorActionPreference = 'Stop'
$pythonPath = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Create .venv and install requirements.txt first. See README.md.'
}

$url = "http://127.0.0.1:$Port"
if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
    throw "Port $Port is already in use. Open $url if Prediqt is already running, or choose -Port."
}

Push-Location $PSScriptRoot
try {
    Write-Host "Prediqt: $url (Ctrl+C to stop)"
    if (-not $NoBrowser) { Start-Process $url }
    & $pythonPath -m uvicorn main:app --host 127.0.0.1 --port $Port
    if ($LASTEXITCODE -ne 0) { throw "Prediqt exited with code $LASTEXITCODE" }
} finally {
    Pop-Location
}
