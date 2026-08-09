$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "LeafyCV1.0 local .venv was not found. Run: py -3.11 -m venv .venv ; .\.venv\Scripts\Activate.ps1 ; python -m pip install -r requirements.txt"
}

$Latest = ".\shared_camera\level1_camera1_latest.jpg"

if (-not (Test-Path $Latest)) {
    Write-Host "Camera 1 latest image is not available yet."
    exit 1
}

& $Python .\cv\leafycv_1_0.py level1_camera1 `
  --latest-image $Latest `
  --output .\outputs\camera1_crowding_test `
  --count 6 `
  --sample-minutes 0.1667
