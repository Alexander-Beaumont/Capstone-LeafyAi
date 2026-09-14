# LeafyAI Full Integration — Zero Camera, one-command local startup

## Quick start

```powershell
docker compose up --build
```

`.env` is optional for a safe local boot. Compose supplies a local-only service account and a sufficiently long development Django secret when values are omitted. Override them in `.env` for shared/Lab environments.

Fresh database behavior: **0 Camera rows**. Camera and LeafyCV services run but stay idle until a user adds a Camera in Plant Vision. Powerboard returns **Not configured** and Sensors stay idle until Lab endpoints/IPs are provided. No camera IP is hard-coded or contacted at startup.

Camera API follows the team **FINAL LOCKED** contract and uses **`farm_level_id`** (integer FarmLevel primary key) for both reads and writes. The Django model relation remains `farm_level`; the serializer maps public `farm_level_id` to that relation.

To reset local Docker data back to zero cameras:

```powershell
docker compose down -v
docker compose up --build
```

# LeafyAI Full Integration — Zero-Camera Start

This package is based on the current `Capstone-LeafyAi` team repository and ports only the proven missing integration behavior from the working MVP. Existing team pages, AI/VLM modules, growth features, backend structure, and routes are retained.

## Non-negotiable fresh-start rule

A fresh database contains **zero Camera rows**. Nothing in source code, `.env.example`, Docker Compose, or the backend seed command creates or connects to `192.168.1.106:554` (or any other camera).

Plant Vision starts with:

> No active camera configured. Add a camera to start Plant Vision.

The physical source is opened only after the user creates an enabled Camera through Plant Vision / `POST /api/cameras/`.

## What was filled from the working MVP

- Full Plant Vision UI: Add/Edit/Enable/Disable/Archive Camera, editable capture interval, English AM/PM active window, ROI drawing, baseline reset, latest official image, exact image-analysis identity matching, pending-analysis state, LeafyCV metric panel.
- Final Camera Backend contract validation and archive lifecycle (`is_archived`).
- Validated official JPEG endpoint: explicit timezone-aware `captured_at`, decodable JPEG check, size limit.
- JSON-only nested `/api/cv/ingest/` validation and read-only generic CameraImage/ImageAnalysis APIs.
- `latest-analysis` includes top-level `image_url` and retains nested `analysis`.
- Camera and LeafyCV worker JWT refresh plus optional username/password login for local/container service accounts.
- Camera and LeafyCV Dockerfiles.
- Sensor worker and Kasa/Lighting service implementation from the verified hardware MVP, without changing the team AI/growth pages.
- Live SensorReadings and Powerboard DeviceControls components while preserving the existing Farm Overview page/AI decision section.
- Docker Compose profiles so hardware services are opt-in.

## Fresh local Backend setup

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_base
python manage.py runserver 8000
```

`seed_base` creates only Farm/FarmDevice/FarmLevel/Sensor identities. It intentionally creates **no Camera**.

Create/login a user through the existing Frontend auth flow. Then open Plant Vision and click **Add Camera**.

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173/plant-vision`.

Before a Camera is added, the page remains empty of camera images/CV results. The Add Camera form does not pre-fill an IP, RTSP port, or RTSP path.

## Camera service

The service reads Camera rows from Backend only. With `GET /api/cameras/ -> []`, it does not call OpenCV/RTSP/Webcam capture.

```powershell
cd <repo-root>
py -3.11 -m venv .venv-camera
.\.venv-camera\Scripts\Activate.ps1
pip install -r camera\requirements.txt
python -m pytest -q camera\tests
python -m camera.main --once
```

## LeafyCV

```powershell
cd LeafyCV1.0
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
python -m pytest -q
python main.py check
```

LeafyCV also reads Backend Camera/Image state only. No Camera means no image and no inference.

## Docker

Copy configuration first:

```powershell
Copy-Item .env.example .env
```

Default stack (Backend + Frontend only):

```powershell
docker compose up --build
```

Vision workers are opt-in:

```powershell
docker compose --profile vision up --build
```

Even with the `vision` profile running, a fresh Backend has zero Camera rows, so no physical camera is contacted until Add Camera is used.

Physical sensor/powerboard services are separately opt-in:

```powershell
docker compose --profile hardware up --build
```

For Camera + Lighting together:

```powershell
docker compose --profile vision --profile hardware up --build
```

Set `LEAFY_LIGHTING_ENABLED=true` only in the Lab when the Powerboard/Lighting service is ready.

## Camera add behavior

For RTSP, the user must explicitly enter:

- IP address
- RTSP port
- RTSP path

Backend rejects an incomplete RTSP Camera; the Camera client also refuses to invent a port/path fallback.

For WEBCAM, the user selects WEBCAM and supplies a webcam index.

## Archive behavior

Remove Camera is archive, not hard delete:

```json
{
  "is_archived": true,
  "enabled": false,
  "cv_enabled": false
}
```

Historical CameraImage/ImageAnalysis rows remain available.

## Do not commit

`.env`, virtual environments, tokens, credentials, generated output, and logs are ignored. Docker persists SQLite/media in named volumes, so the repository ships with no `runtime/` directory.
