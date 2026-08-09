$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "LeafyCV1.0 local .venv was not found. Run: py -3.11 -m venv .venv ; .\.venv\Scripts\Activate.ps1 ; python -m pip install -r requirements.txt"
}

& $Python .\check_setup.py
