# LeafyCV1.0 - Final Computer Vision Handover

LeafyCV1.0 is the Computer Vision subsystem for the Leafy AI sweet-basil hydroponic vertical farm.

The final operating rule is simple:

```text
LIVE CAMERA PREVIEW
        |
        | continuous display only
        | no historical database write
        |
        +---- every 30 minutes ----> ONE SAVED CV SAMPLE
                                      |
                                      +-> canopy
                                      +-> visibility
                                      +-> width / height
                                      +-> crowding
                                      +-> growth change
                                      +-> optional colour values
                                      +-> Django/database ingest
```

The live preview is for monitoring, ROI/SLOT alignment and calibration. Numeric CV history is produced only by scheduled or manually requested saved analyses.

## 1. Folder structure

```text
LeafyCV1.0/
├── main.py                  Run this file
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── configs/                 Standalone/demo camera configurations
├── demo/                    Offline NORMAL and MAGENTA test images
├── docs/                    Team integration handover PDF
├── leafycv/                 Internal CV modules
└── tests/                   Regression tests
```

Do not run files inside `leafycv/` directly. Use `main.py`.

## 2. What LeafyCV measures

- fixed physical SLOT identity from registered camera coordinates;
- whole-ROI canopy coverage;
- per-SLOT canopy coverage;
- per-SLOT visibility;
- plant width and height in pixels;
- width and height in centimetres when a calibration stick is configured;
- crowding based on neighbouring SLOT canopy contact;
- growth change relative to the previous valid saved sample;
- green/yellow estimates under NORMAL lighting only;
- image-quality validity checks.

Lighting profiles:

```text
NORMAL
MAGENTA
```

Under MAGENTA lighting, normal-light green/yellow values are returned as `null`.

## 3. First-time Windows setup

Open PowerShell in the folder containing `main.py`.

```powershell
py -3.11 -m venv .venv
```

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Check the installation:

```powershell
.\.venv\Scripts\python.exe main.py check
```

Run the included offline tests:

```powershell
.\.venv\Scripts\python.exe -m unittest discover tests -v
```

## 4. Offline demo

NORMAL:

```powershell
.\.venv\Scripts\python.exe main.py demo --mode NORMAL
```

MAGENTA:

```powershell
.\.venv\Scripts\python.exe main.py demo --mode MAGENTA
```

Outputs are created automatically under `outputs/`.

## 5. Standalone webcam test

Create a webcam configuration:

```powershell
.\.venv\Scripts\python.exe main.py create-config `
  --output configs\my_webcam.json `
  --camera-name "My Webcam" `
  --source-type WEBCAM `
  --webcam-index 0 `
  --lighting NORMAL
```

Test one frame:

```powershell
.\.venv\Scripts\python.exe main.py test-source `
  --config configs\my_webcam.json `
  --show
```

If index `0` is not the required camera, recreate the config with `--webcam-index 1` or another valid index and add `--overwrite`.

## 6. Standalone calibration

Example with three temporary SLOT IDs and a 20 cm reference:

```powershell
.\.venv\Scripts\python.exe main.py calibrate `
  --config configs\my_webcam.json `
  --slot-count 3 `
  --reference-length-cm 20
```

The calibration workflow sets:

1. monitoring ROI;
2. SLOT centre positions;
3. optional calibration-stick endpoints and real length.

For database integration, use the real database SLOT UUIDs instead of temporary `1,2,3`:

```powershell
.\.venv\Scripts\python.exe main.py calibrate `
  --config configs\my_webcam.json `
  --slot-ids "UUID_P01,UUID_P02,UUID_P03" `
  --reference-length-cm 20
```

## 7. Final live behaviour on a laptop webcam

Use `monitor` when you want the camera to remain visible while CV data is saved only at the scheduled interval.

```powershell
.\.venv\Scripts\python.exe main.py monitor `
  --config configs\my_webcam.json `
  --interval-minutes 30 `
  --slot-count 3 `
  --reference-length-cm 20
```

The monitor window displays live frames continuously. It does not run/save CV on every displayed frame.

Controls in local-config monitor mode:

```text
Q / ESC   Quit
SPACE     Pause/resume preview
S         Save one official CV sample now
R         Set/adjust ROI
P         Register/re-register SLOT positions
C         Set/adjust calibration stick
X         Remove calibration stick
N         NORMAL lighting
M         MAGENTA lighting
```

The screen always labels the timestamp of the latest saved analysis. Between scheduled analyses, the numeric values remain the last saved result.

For faster development testing, temporarily use:

```powershell
--interval-minutes 1
```

Return to `30` for the final system.

## 8. Official one-shot and scheduled modes

Save one official sample:

```powershell
.\.venv\Scripts\python.exe main.py run-once `
  --config configs\my_webcam.json
```

Run one saved sample every 30 minutes:

```powershell
.\.venv\Scripts\python.exe main.py run-loop `
  --config configs\my_webcam.json `
  --interval-minutes 30
```

`run-loop` is the recommended LeafyCV process for the final lab RTSP deployment because each scheduled capture opens the camera, obtains a fresh frame and releases the connection before waiting for the next interval.

## 9. Integrated Django/database mode

In the final team integration, React saves camera/ROI/calibration/SLOT configuration to Django/database. LeafyCV can read the current database-backed configuration directly from the backend.

Required backend routes are described in `docs/LeafyCV1.0_Integration_Handover_Guide.pdf`.

Example integrated one-shot:

```powershell
.\.venv\Scripts\python.exe main.py run-once `
  --backend-base-url http://127.0.0.1:8000 `
  --camera-id YOUR_CAMERA_UUID
```

Example integrated 30-minute production scheduler:

```powershell
.\.venv\Scripts\python.exe main.py run-loop `
  --backend-base-url http://127.0.0.1:8000 `
  --camera-id YOUR_CAMERA_UUID `
  --interval-minutes 30
```

In integrated mode LeafyCV reads:

```text
GET /api/cv/cameras/{camera_id}/config/
GET /api/cv/cameras/{camera_id}/slot-positions/
```

and sends each official sample to:

```text
POST /api/cv/ingest/
```

The backend stores:

```text
CAMERAIMAGE
    -> IMAGEANALYSIS
        -> PLANTVISIONMEASUREMENT for each SLOT
```

## 10. React live preview in the final lab system

The final React page should display the live/transient preview through the backend:

```text
GET /api/cv/cameras/{camera_id}/preview/
```

The live preview is independent from the 30-minute saved CV results.

React also reads the latest saved result from:

```text
GET /api/cv/cameras/{camera_id}/latest-analysis/
```

The UI should clearly display, for example:

```text
Live Camera
Last analysed: 16:30
Next scheduled analysis: 17:00
Visible plants: 18
Canopy coverage: 64.2%
```

## 11. Lab RTSP connection

Connect the LeafyCV computer/server to the isolated `Leafy_AI` lab network.

Set the read-only camera credentials in the local environment:

```powershell
$env:FARM_CAMERA_USER='YOUR_USERNAME'
$env:FARM_CAMERA_PASSWORD='YOUR_PASSWORD'
```

The final configuration/database provides the camera IP, RTSP port/path and lighting mode.

For scheduled CV operation, use `run-loop --interval-minutes 30`. Do not use an unbounded direct RTSP `monitor` process as the normal production collector. The backend/shared camera preview service should provide the live React image while LeafyCV performs the bounded scheduled capture-and-release workflow.

## 12. Output files

For every official analysis LeafyCV saves local recovery/debug files under:

```text
outputs/<camera_name>/
```

Typical files:

```text
*_raw.jpg
*_annotated.jpg
*_mask.png
*_result.json
measurements.csv
state.json
```

`state.json` preserves the previous valid per-SLOT baseline used for growth calculation across process restarts.

## 13. Backend failure behaviour

LeafyCV saves local output first. If the Django API is unavailable, the local CV result remains available and the program prints a warning rather than discarding the sample.

## 14. Handover acceptance check

Before final deployment confirm:

- `python main.py check` succeeds;
- all tests pass;
- NORMAL demo succeeds;
- MAGENTA demo succeeds;
- webcam source test succeeds;
- ROI and SLOT registration are correct;
- calibration stick produces sensible centimetre values;
- `monitor` shows live frames while saved values change only at the scheduled interval;
- backend-driven config loads using a real CAMERA UUID;
- one `run-once` creates the expected CameraImage -> ImageAnalysis -> PlantVisionMeasurement records;
- the final scheduler uses a 30-minute interval;
- React live preview shows the latest saved-analysis timestamp separately from the live image.

For the exact frontend/backend/database interface, read the integration handover PDF in `docs/`.
