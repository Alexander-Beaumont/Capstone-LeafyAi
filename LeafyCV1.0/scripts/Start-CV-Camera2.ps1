$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "LeafyCV1.0 local .venv was not found. Run: py -3.11 -m venv .venv ; .\.venv\Scripts\Activate.ps1 ; python -m pip install -r requirements.txt"
}

$Latest = ".\shared_camera\level1_camera2_latest.jpg"

if (-not (Test-Path $Latest)) {
    Write-Host "Camera 2 latest image does not exist yet:"
    Write-Host $Latest
    Write-Host "Start the approved shared camera service first and wait for Camera 2."
    exit 1
}

& $Python .\cv\leafycv_1_0.py level1_camera2 `
  --latest-image $Latest `
  --output .\outputs\camera2 `
  --count 144 `
  --sample-minutes 10
