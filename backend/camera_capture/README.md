# Leafy AI camera_capture

`camera_capture` is the integration boundary between the physical LeafyAI farm camera and Leafy AI's internal Django storage.

It is responsible for acquiring images from the farm camera over RTSP, performing technical image-quality checks, storing accepted captures, and making those images available to downstream VLM/AI processing.

It deliberately **does not** decide plant health, growth state or farm actions.

Plant interpretation belongs to the VLM/AI layer.

Lighting control belongs to the powerboard subsystem and is independent from camera capture.

The previous camera-lighting coupling has been removed.

---

## Current status

Status: **Implemented and hardware tested**

The current camera integration has been tested against the physical LeafyAI farm camera.

Tested device:

| Setting | Tested value |
| --- | --- |
| Camera IP | `192.168.1.108` |
| RTSP port | `554` |
| RTSP path | `/stream1` |
| Protocol | RTSP |
| Capture backend | OpenCV |

A direct RTSP capture was successfully verified against the physical camera.

A successful test returned a valid OpenCV frame with dimensions:

```text
(1616, 2880, 3)
```

This confirms the physical path:

```text
Camera
  -> RTSP
  -> OpenCV
  -> LeafyAI backend
```

---

## Final architecture

The intended camera flow is:

```text
Physical RTSP Camera
192.168.1.108:554/stream1
        |
        | RTSP
        v
 camera_client
        |
        v
 camera_collector
        |
        v
 technical image-quality gate
        |
        +---- quality_status
        +---- quality_flags
        +---- quality_message
        +---- quality_metrics
        +---- vlm_ready
        |
        v
 telemetry.CameraImage
        |
        v
 VLM / AI layer
        |
        v
 Recommendation / frontend
```

The camera subsystem is responsible for:

```text
capture
-> technical quality validation
-> persistence
-> VLM readiness
```

It is not responsible for plant interpretation.

---

## Responsibility boundary

`camera_capture` should remain focused on physical image acquisition.

It may perform technical checks required to determine whether an image is usable.

Examples include:

```text
image availability
frame validity
brightness / exposure problems
blur or poor image quality
colour-cast detection
technical capture failures
```

These checks determine whether an image is suitable for downstream processing.

They must not become a duplicate plant-analysis system.

The intended separation is:

```text
camera_capture
    -> Is this image technically usable?

VLM / AI
    -> What does this image mean for the plants/farm?
```

---

## Camera configuration

The currently tested LeafyAI camera configuration is:

```env
LEAFY_CAMERA_1_NAME=Camera Level 1
LEAFY_CAMERA_1_LEVEL=1

LEAFY_CAMERA_1_IP=192.168.1.108
LEAFY_CAMERA_1_RTSP_PORT=554
LEAFY_CAMERA_1_RTSP_PATH=/stream1

LEAFY_CAMERA_1_CAPTURE_INTERVAL_MINUTES=30
LEAFY_CAMERA_1_ENABLED=true

LEAFY_CAMERA_TIMEZONE=Australia/Melbourne
LEAFY_CAMERA_POLL_SECONDS=30

LEAFY_CAMERA_JPEG_QUALITY=92
LEAFY_CAMERA_WARMUP_FRAMES=12

FARM_CAMERA_USER=
FARM_CAMERA_PASSWORD=
```

For the current local development workflow, these values are read from the repository-root:

```text
.env.example
```

Do not commit real camera usernames or passwords into `.env.example`.

If credentials are required in deployment, provide them using the deployment environment.

---

The camera has no CV enable/disable setting. Its fixed responsibility is:

```text
CameraImage
    -> technical image-quality gate
    -> VLM
```

rather than:

```text
CameraImage
    -> traditional CV analysis
    -> VLM
```

---

## Important files

The active camera-capture files are:

```text
camera_capture/
├── tests/
│   ├── test_multi_camera_batch.py
│   ├── test_quality_gate.py
│   └── test_schedule.py
├── apps.py
├── camera_client.py
├── camera_collector.py
├── config.py
├── quality.py
├── repository.py
├── services.py
└── README.md
```

### `camera_client.py`

Responsibilities:

- Build/use the RTSP camera connection.
- Open the physical camera stream.
- Read fresh OpenCV frames.
- Report capture failures cleanly.

The camera client should remain independent from lighting control.

---

### `camera_collector.py`

Responsibilities:

- Determine which configured cameras require capture.
- Request fresh frames from the camera client.
- Run technical image-quality checks.
- Persist accepted image files.
- Create/update `CameraImage` records.
- Record image-quality metadata.

---

### `quality.py`

Responsibilities:

- Perform technical image-quality checks.
- Produce quality status and flags.
- Determine whether the image is suitable for downstream VLM processing.

This module must not become responsible for plant-health interpretation.

---

### `repository.py`

Responsibilities:

- Handle persistence-related operations required by the camera collector.
- Keep database and file-storage behaviour separated from physical RTSP acquisition.

---

### `services.py`

Responsibilities:

- Construct the camera collector from the current configuration.
- Expose the application-level camera collection workflow.

---

### `config.py`

Responsibilities:

- Load camera-related configuration.
- Validate capture and scheduling configuration.
- Provide runtime settings to the camera subsystem.

---

## CameraImage data contract

Captured images are represented by:

```text
telemetry.CameraImage
```

Important image-quality fields include:

```text
quality_status
quality_flags
quality_message
quality_metrics
vlm_ready
```

The purpose of these fields is to preserve the result of the technical quality gate.

Conceptually:

```text
quality_status
    -> overall technical image-quality state

quality_flags
    -> individual detected quality problems

quality_message
    -> human-readable quality information

quality_metrics
    -> measured technical image characteristics

vlm_ready
    -> whether the image is suitable for downstream VLM processing
```

The quality gate must not overwrite or replace the original captured image simply because the image is unsuitable for VLM analysis.

---

## VLM handoff

The desired downstream architecture is:

```text
CameraImage
    |
    +---- captured image
    +---- captured_at
    +---- quality metadata
    +---- vlm_ready
    |
    v
VLM / AI layer
```

The VLM should consume an image only when the downstream workflow considers it appropriate.

`camera_capture` is responsible for preparing the image.

The VLM/AI layer is responsible for interpreting it.

Examples of plant interpretation that should not be implemented in `camera_capture` include:

```text
plant health assessment
growth-stage interpretation
nutrient-deficiency interpretation
disease interpretation
crop recommendations
farm actions
```

---

## Removed camera-lighting coupling

The previous camera implementation included:

```text
camera_capture/lighting_client.py
```

and:

```text
camera_capture/tests/test_lighting_contract.py
```

These components have been removed.

Camera capture must not turn the farm lights on or off.

The final responsibility split is:

```text
camera_capture
    -> capture images

powerboard_control
    -> control physical lights
```

The camera may capture while the current farm lighting state exists, but it must not change that state as part of the capture workflow.

Do not reintroduce:

```text
turn lights on
-> wait
-> capture
-> restore lights
```

unless the project requirements are explicitly changed by the team.

---

## Why lighting control was removed

Lighting is a farm actuator responsibility.

Coupling it to camera capture created unnecessary dependencies between:

```text
Camera availability
Powerboard availability
Lighting state
Image acquisition
```

The current design keeps those systems independent.

This means a camera capture failure does not alter lighting state, and lighting-control failures do not have to prevent the camera subsystem from attempting image capture.

---

## One-time local setup

### Windows PowerShell

From the repository root:

```powershell
python -m venv .venv
```

Activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r .\backend\requirements.txt
```

Enter the backend:

```powershell
cd backend
```

Apply migrations:

```powershell
python manage.py migrate
```

Bootstrap the LeafyAI configuration:

```powershell
python manage.py bootstrap_leafy
```

If the camera configuration is present, `bootstrap_leafy` creates or updates the configured Camera record.

---

## Local test without farm hardware

The physical camera uses a private Lab-network address:

```text
192.168.1.108
```

The camera is normally unreachable when developing outside the LeafyAI Lab.

Disable the physical background runtime:

```powershell
$env:LEAFY_RUNTIME_ENABLED="false"
```

Run the Django system check:

```powershell
python manage.py check
```

Run camera tests:

```powershell
python manage.py test camera_capture
```

The backend can then be started without automatically attempting physical Camera/Sensor background collection:

```powershell
python manage.py runserver 0.0.0.0:8000 --noreload
```

Expected startup output includes:

```text
Leafy AI background runtime disabled by LEAFY_RUNTIME_ENABLED.
System check identified no issues (0 silenced).
```

To restore the configured runtime behaviour:

```powershell
Remove-Item Env:LEAFY_RUNTIME_ENABLED
```

---

## Lab RTSP connectivity test

This test must be performed while connected to the LeafyAI Lab network.

Activate the virtual environment and enter the backend:

```powershell
.\.venv\Scripts\Activate.ps1
cd backend
```

A simple direct OpenCV RTSP test can be used:

```powershell
python -c "import cv2; url='rtsp://192.168.1.108:554/stream1'; cap=cv2.VideoCapture(url); ok, frame=cap.read(); print('success=', ok); print('shape=', None if frame is None else frame.shape); cap.release()"
```

A successful result should report:

```text
success= True
```

and a non-empty frame shape.

The physical LeafyAI camera has previously returned:

```text
(1616, 2880, 3)
```

A different valid resolution does not automatically indicate a failure if the physical camera configuration changes.

---

## Lab collector test

Before running the collector:

```powershell
python manage.py migrate
python manage.py bootstrap_leafy
```

Then a forced camera collection can be triggered through the Django shell:

```powershell
python manage.py shell -c "from camera_capture.services import build_collector; print(build_collector().process_all(force=True))"
```

A successful capture should result in:

```text
RTSP frame acquired
        |
        v
image-quality evaluation
        |
        v
JPEG stored under backend/media/
        |
        v
CameraImage database record
```

---

## Verify stored CameraImage

Captured image records can be inspected from Django:

```powershell
python manage.py shell
```

Example:

```python
from telemetry.models import CameraImage

for image in CameraImage.objects.order_by("-captured_at")[:5]:
    print(
        image.id,
        image.camera_id,
        image.path,
        image.captured_at,
        image.quality_status,
        image.quality_flags,
        image.vlm_ready,
    )
```

This allows the team to confirm that:

```text
capture succeeded
image path was persisted
quality metadata was stored
vlm_ready was calculated
```

---

## Media storage

Generated camera images are stored under:

```text
backend/media/camera_images/
```

These files are runtime data.

They must not be committed to Git.

The repository `.gitignore` should contain:

```gitignore
backend/media/
```

The camera subsystem recreates the required storage path when new image files are persisted.

Do not commit captured Lab images as backend source code.

---

## Image quality versus plant analysis

The camera quality gate and plant interpretation are separate concerns.

### Image-quality gate

Examples:

```text
Can the image be read?
Is the frame technically usable?
Is exposure acceptable?
Is the image severely blurred?
Is a technical colour cast detected?
```

Output:

```text
quality_status
quality_flags
quality_message
quality_metrics
vlm_ready
```

### VLM analysis

Examples:

```text
What is happening to the plant?
Does the plant show visible stress?
What growth observations can be made?
What recommendation should be generated?
```

These belong downstream in the VLM/AI subsystem.

---

## Background runtime

The LeafyAI runtime can automatically poll configured cameras when:

```env
LEAFY_RUNTIME_ENABLED=true
```

Relevant scheduling settings include:

```env
LEAFY_CAMERA_1_CAPTURE_INTERVAL_MINUTES=30
LEAFY_CAMERA_POLL_SECONDS=30
```

Conceptually:

```text
runtime poll
    |
    v
is camera due?
    |
   yes
    |
    v
capture fresh frame
    |
    v
quality gate
    |
    v
store CameraImage
```

The runtime should not capture continuously on every web request.

Camera collection is a background hardware workflow.

---

## Camera scheduling

The configured capture interval and runtime polling interval have different responsibilities.

Example:

```env
LEAFY_CAMERA_1_CAPTURE_INTERVAL_MINUTES=30
LEAFY_CAMERA_POLL_SECONDS=30
```

This means the runtime may check approximately every 30 seconds whether a Camera is due, while the Camera itself is scheduled to capture approximately every 30 minutes.

Do not interpret:

```text
LEAFY_CAMERA_POLL_SECONDS
```

as the required image-capture frequency.

---

## Time handling

The application timezone is:

```text
Australia/Melbourne
```

Django database timestamps should remain timezone-aware.

Do not manually convert database timestamps before persistence.

For local display:

```python
from django.utils import timezone

timezone.localtime(image.captured_at)
```

This allows Django to handle Melbourne daylight-saving changes correctly.

---

## Known environment behaviour

The tested camera address is:

```text
192.168.1.108
```

This is a private Lab-network address.

When working from another network:

```text
RTSP timeout
connection refused
camera unreachable
```

does not by itself mean the camera code is broken.

Hardware connectivity must be validated from the Lab network.

Local software tests and physical hardware tests should therefore be treated separately.

---

## Tests

### Local software tests

With physical runtime disabled:

```powershell
$env:LEAFY_RUNTIME_ENABLED="false"
python manage.py test camera_capture
```

These tests validate camera scheduling, quality logic and collection behaviour without requiring the physical farm camera where mocks are used.

### Physical Lab test

Use:

```powershell
python -c "import cv2; url='rtsp://192.168.1.108:554/stream1'; cap=cv2.VideoCapture(url); ok, frame=cap.read(); print(ok, None if frame is None else frame.shape); cap.release()"
```

followed by:

```powershell
python manage.py shell -c "from camera_capture.services import build_collector; print(build_collector().process_all(force=True))"
```

The two test types serve different purposes:

```text
Local tests
    -> verify backend camera logic

Lab RTSP test
    -> verify physical camera/network connection

Lab collector test
    -> verify full Camera -> backend persistence path
```

---

## Runtime files

The following local files should not be committed:

```text
.venv/
backend/db.sqlite3
backend/media/
__pycache__/
*.pyc
```

They should be covered by `.gitignore`.

The database can be regenerated using:

```powershell
python manage.py migrate
python manage.py bootstrap_leafy
```

Camera images are regenerated through normal capture.

---

## Handover checklist

Before merging Camera changes, confirm:

- [ ] RTSP is still the physical camera transport.
- [ ] The configured Lab camera is `192.168.1.108`.
- [ ] RTSP port remains `554` unless hardware configuration changes.
- [ ] RTSP path remains `/stream1` unless hardware configuration changes.
- [ ] Direct RTSP capture works in the Lab.
- [ ] Camera capture does not control the farm lights.
- [ ] `lighting_client.py` has not been reintroduced.
- [ ] `test_lighting_contract.py` has not been reintroduced.
- [ ] Lighting remains under `powerboard_control`.
- [ ] Technical image-quality checks remain active.
- [ ] `CameraImage` stores image-quality metadata.
- [ ] `vlm_ready` remains available for downstream processing.
- [ ] Plant interpretation remains outside `camera_capture`.
- [ ] Local testing works with `LEAFY_RUNTIME_ENABLED=false`.
- [ ] Camera tests pass.
- [ ] Lab collector testing creates a `CameraImage`.
- [ ] Generated images under `backend/media/` are not committed.
- [ ] `db.sqlite3`, `.venv` and Python cache files are not committed.

---

## Final handover state

The expected camera architecture is:

```text
LeafyAI RTSP Camera
        |
        v
camera_client
        |
        v
camera_collector
        |
        v
technical image-quality gate
        |
        v
telemetry.CameraImage
        |
        v
VLM / AI
        |
        v
Recommendation / frontend
```

The camera subsystem does not control lighting.

The camera subsystem does not perform plant-health interpretation.

Lighting is controlled independently by:

```text
powerboard_control
```

Plant interpretation is handled downstream by:

```text
VLM / AI layer
```

The RTSP camera integration has been tested successfully against the physical LeafyAI farm camera.
