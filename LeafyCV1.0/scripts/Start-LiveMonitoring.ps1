$ErrorActionPreference = "Stop"
$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    throw "LeafyCV1.0 local .venv was not found. Run: py -3.11 -m venv .venv ; .\.venv\Scripts\Activate.ps1 ; python -m pip install -r requirements.txt"
}

Write-Host ""
Write-Host "LeafyCV1.0 - Shared Camera Services"
Write-Host "Use continuous shared RTSP only when this machine is the approved/trusted collector."
Write-Host ""

if (-not $env:FARM_CAMERA1_IP -or -not $env:FARM_CAMERA2_IP) {
    throw "Set FARM_CAMERA1_IP and FARM_CAMERA2_IP locally in PowerShell first."
}

if (-not $env:FARM_CAMERA_USER) {
    $env:FARM_CAMERA_USER = Read-Host "Camera username"
}

if (-not $env:FARM_CAMERA_PASSWORD) {
    $SecurePassword = Read-Host "Camera password" -AsSecureString
    $Ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecurePassword)
    try {
        $env:FARM_CAMERA_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($Ptr)
    }
    finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($Ptr)
    }
}

if ($null -eq $env:FARM_CAMERA_RTSP_PATH) {
    $env:FARM_CAMERA_RTSP_PATH = Read-Host "RTSP path (press Enter for empty)"
}

Write-Host "Checking camera RTSP ports..."
$Cam1 = Test-NetConnection -ComputerName $env:FARM_CAMERA1_IP -Port 554 -WarningAction SilentlyContinue
$Cam2 = Test-NetConnection -ComputerName $env:FARM_CAMERA2_IP -Port 554 -WarningAction SilentlyContinue
Write-Host "Camera 1 $($env:FARM_CAMERA1_IP):554 =" $Cam1.TcpTestSucceeded
Write-Host "Camera 2 $($env:FARM_CAMERA2_IP):554 =" $Cam2.TcpTestSucceeded

if (-not $Cam1.TcpTestSucceeded -or -not $Cam2.TcpTestSucceeded) {
    Write-Warning "At least one camera is not reachable. Check farm network/IP/firewall before continuing."
}

Start-Process powershell -WorkingDirectory $ProjectRoot -ArgumentList @(
    "-NoExit",
    "-Command",
    "& `"$Python`" `".\camera\farm_camera_shared_service.py`" level1_camera1 --host 127.0.0.1 --port 8001 --publish-fps 1"
)

Start-Process powershell -WorkingDirectory $ProjectRoot -ArgumentList @(
    "-NoExit",
    "-Command",
    "& `"$Python`" `".\camera\farm_camera_shared_service.py`" level1_camera2 --host 127.0.0.1 --port 8002 --publish-fps 1"
)

Write-Host ""
Write-Host "LeafyCV1.0 shared camera services started."
Write-Host "Camera 1 local service: http://127.0.0.1:8001/"
Write-Host "Camera 2 local service: http://127.0.0.1:8002/"
Write-Host "No frontend/dashboard is included in LeafyCV1.0."
