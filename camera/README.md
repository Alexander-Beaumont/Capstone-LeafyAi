# Leafy Camera - Standalone MVP Service

This folder is a standalone camera acquisition component. It does **not** import Django models and does **not** perform computer vision.

## Runtime boundary

```text
RTSP / WEBCAM
      |
      v
camera service
      |
      | POST JPEG
      v
Django Backend -> CameraImage -> LeafyCV
```

## Backend API required

```text
GET  /api/cameras/
GET  /api/cameras/{camera_id}/
GET  /api/cv/cameras/{camera_id}/latest-image/
POST /api/cameras/{camera_id}/official-image/
```

The Camera model must expose `enabled`, `cv_enabled`, `capture_interval_minutes`, `active_start_time`, and `active_end_time`.

## Install

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r camera\requirements.txt
```

## Local webcam smoke test

This does not need Django:

```powershell
python -m camera.test_local_webcam --index 0
```

The webcam helper attempts common resolutions from highest to lowest and uses the best mode accepted by the driver.

## Camera service environment

```powershell
$env:LEAFY_BACKEND_BASE_URL="http://127.0.0.1:8000"
$env:LEAFY_BACKEND_ACCESS_TOKEN="<JWT access token>"
$env:LEAFY_BACKEND_REFRESH_TOKEN="<JWT refresh token>"
$env:LEAFY_CAMERA_TIMEZONE="Australia/Melbourne"
```

RTSP credentials must not be committed:

```powershell
$env:FARM_CAMERA_USER="camera_viewer"
$env:FARM_CAMERA_PASSWORD="..."
```

Optional per-camera credentials:

```powershell
$env:CAMERA_1_USER="camera_viewer"
$env:CAMERA_1_PASSWORD="..."
```

## Manual end-to-end camera test

Bypass schedule for one camera:

```powershell
python -m camera.main --once --camera-id 1 --force
```

Expected result: backend creates one official `CameraImage`.

## Production-style loop

```powershell
python -m camera.main
```

The service polls backend configuration but only captures when the configured interval is due and the current local time is inside the active window.

Default capture interval belongs in the backend database (`30` minutes), not hard-coded into the CV service.
