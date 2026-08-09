$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "LeafyCV1.0 local .venv was not found. Run: py -3.11 -m venv .venv ; .\.venv\Scripts\Activate.ps1 ; python -m pip install -r requirements.txt"
}

if (-not $env:LEAFY_CV_API_URL) {
    $env:LEAFY_CV_API_URL = Read-Host "Exact backend CV API URL"
}

if (-not $env:LEAFY_CV_API_SEND_IMAGES) {
    $env:LEAFY_CV_API_SEND_IMAGES = "raw"
}

if (-not (Test-Path ".\shared_camera\level1_camera1_latest.jpg") -or
    -not (Test-Path ".\shared_camera\level1_camera2_latest.jpg")) {
    Write-Host "Both latest camera images are required."
    Write-Host "Start the approved shared camera services first."
    exit 1
}

Start-Process powershell -WorkingDirectory $ProjectRoot -ArgumentList @(
    "-NoExit",
    "-Command",
    "& `"$Python`" `".\cv\leafycv_1_0.py`" level1_camera1 --latest-image `".\shared_camera\level1_camera1_latest.jpg`" --output `".\outputs\camera1`" --count 144 --sample-minutes 10"
)

Start-Process powershell -WorkingDirectory $ProjectRoot -ArgumentList @(
    "-NoExit",
    "-Command",
    "& `"$Python`" `".\cv\leafycv_1_0.py`" level1_camera2 --latest-image `".\shared_camera\level1_camera2_latest.jpg`" --output `".\outputs\camera2`" --count 144 --sample-minutes 10"
)

Write-Host "LeafyCV1.0: both CV workers started with backend API output."
Write-Host "API URL:" $env:LEAFY_CV_API_URL
Write-Host "Image mode:" $env:LEAFY_CV_API_SEND_IMAGES
