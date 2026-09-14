# LeafyAI

LeafyAI is a vertical-farm monitoring and control project. The current repository keeps Django as the API/database/authentication owner while Camera, Sensor, Powerboard, and LeafyCV run as separate workers/services.

This README is the single project-level source of truth for setup, runtime boundaries, Camera/CV contracts, and handoff notes. Database structure is documented separately in `database_schema_v2.md`.

## 1. Current architecture

```text
Physical RTSP Camera
        |
        v
Camera Capture Worker
        |
        v
Django Backend ---- Database
        |
        v
CameraImage
        |
        v
LeafyCV Worker
        |
        v
analysis JSON
        |
        v
Django Backend
        |
        v
ImageAnalysis
        |
        v
Frontend
```

Sensors and Powerboard also integrate through the Backend. Hardware loops do **not** run inside the Django web process.

Source layout:

```text
LeafyAI/
├── backend/
│   ├── accounts/
│   ├── ai_agent/
│   ├── camera_capture/       # RTSP capture/scheduler worker
│   ├── core/                 # Django project
│   ├── cv/                   # CV API + ImageAnalysis persistence
│   ├── farm_state/
│   ├── growth/
│   ├── powerboard_control/   # separate powerboard/lighting service
│   ├── sensor_ingest/        # separate sensor worker
│   ├── telemetry/
│   └── vlm_agent/
├── frontend/
├── LeafyCV1.0/               # separate ML inference worker
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
└── database_schema_v2.md
```

Runtime services remain separate:

```text
backend
frontend
camera
sensors
powerboard
leafycv
```

Moving worker source under `backend/` is repository organisation only. It does not move those loops into Django and does not redesign the Camera/CV API.

## 2. Quick start

From the repository root:

```bash
docker compose up --build
```

Optional local overrides can be placed in `.env` by copying `.env.example`. Do not commit `.env` or real hardware credentials.

Useful endpoints during local development:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Backend health: `http://localhost:8000/health/`
- Powerboard service: `http://localhost:8010`

To reset local Docker database/media volumes:

```bash
docker compose down -v
docker compose up --build
```

A fresh database must not contain a preconfigured Lab Camera, CameraImage, ImageAnalysis, or fake SensorReading. Base farm metadata/service identities may be seeded by Backend startup.

## 3. Backend responsibility

Django owns:

- API contracts
- authentication/JWT
- validation
- database persistence and history
- Camera configuration
- official image records
- CV result ingestion
- farm/growth state
- integration boundaries used by Frontend and workers

Workers should use Backend APIs instead of writing the database directly.

## 4. Camera — RTSP only

Camera support is RTSP-only. Webcam/USB camera runtime support has been removed.

Current Camera API uses public field `farm_level_id`. The Django model relation may remain `farm_level`; serializers map the public ID to that relation.

Important Camera fields:

```text
id
farm_level_id
name
position
source_type              # RTSP
ip_address
rtsp_port
rtsp_path
enabled
cv_enabled
is_archived
capture_interval_minutes
active_start_time
active_end_time
roi_points
growth_baseline_reset_at
```

No Lab Camera IP is auto-seeded. A Camera should be created through the API/UI.

Core Camera endpoints:

```text
GET/POST   /api/cameras/
GET/PATCH  /api/cameras/{id}/
POST       /api/cameras/{id}/official-image/
```

### Scheduler rule

A Camera is eligible when:

```text
enabled
AND cv_enabled
AND inside active window
AND (
    no previous official image
    OR now - latest captured_at >= capture_interval_minutes
)
```

The scheduler does not use wall-clock anchors and does not backfill missed captures. A failed capture creates no CameraImage and is retried on a later poll.

Active-window semantics:

```text
start < end   normal daytime window
start > end   overnight window
both null     24-hour operation
start == end  invalid at API validation level
```

Historical migrations may still mention `WEBCAM`; keep migration history intact.

## 5. Official image contract

The Camera worker posts one JPEG to:

```text
POST /api/cameras/{id}/official-image/
```

The Backend should require a timezone-aware `captured_at`, validate that the uploaded content is a real JPEG within the allowed size, create exactly one CameraImage, and return without running ML inference inside the request.

CameraImage stores an image path/file field rather than a database blob.

## 6. LeafyCV

`LeafyCV1.0/` stays separate from Django because PyTorch/OpenCV/model inference is a distinct workload.

Locked model/preprocessing assumptions currently used by the project:

```text
Binary semantic U-Net
EfficientNet-B0 encoder
512x512 RGB
classes = 1
threshold = 0.5
checkpoint = models/leafy_canopy_effnet_b0_final.pth
BGR -> RGB
resize to 512
float / 255
no ImageNet normalization
encoder_weights = None
```

Do not rewrite the model, checkpoint, threshold, or preprocessing during repository cleanup/refactoring.

Current analysis metrics include:

```text
total_canopy_coverage
growth_change
crowding_percentage
green_percentage
yellow_percentage
measurement_valid
processing_time_ms
vlm_ready
quality_status
quality_flags
quality_message
```

The worker reads official CameraImages from Backend and sends results back to Backend. It does not open RTSP streams or own lighting control.

## 7. CV API contract

Core CV endpoints:

```text
GET  /api/cv/cameras/{id}/latest-image/
GET  /api/cv/cameras/{id}/latest-analysis/
GET  /api/cv/cameras/{id}/latest-analysis/?valid=true
POST /api/cv/ingest/
```

Expected ingest shape:

```json
{
  "camera_id": 1,
  "image_id": 152,
  "analysis": {
    "total_canopy_coverage": 37.5,
    "growth_change": null,
    "crowding_percentage": 31.4,
    "green_percentage": 86.2,
    "yellow_percentage": 4.8,
    "measurement_valid": false,
    "processing_time_ms": 105,
    "vlm_ready": false,
    "quality_status": "FAIL",
    "quality_flags": ["MAGENTA_CAST"],
    "quality_message": "..."
  }
}
```

Backend validation should ensure that the image belongs to the supplied Camera, percentage values are within `0..100`, duplicate ImageAnalysis creation is rejected, and CV ingest remains JSON-only.

`ImageAnalysis` has no direct Camera foreign key. Query Camera identity through:

```text
ImageAnalysis -> image -> camera
```

The latest-analysis response should atomically describe the matching image and analysis so Frontend never pairs a newer image with an older analysis. If a newer CameraImage exists without an ImageAnalysis, Frontend should display an analysis-pending state.

## 8. Growth baseline reset

`growth_baseline_reset_at` marks the point after which growth comparison should restart. The first valid analysis after a reset has `growth_change = null`; subsequent valid images compare against the new post-reset baseline.

Use a reset for material scene changes such as camera repositioning, plant replacement/rearrangement, major ROI changes, or transfers. Changing capture interval alone should not reset growth history.

## 9. Sensors

`backend/sensor_ingest/` is a separate polling/ingest worker and should send readings through Backend APIs.

Historical SensorReadings should remain stored. Frontend live status should use reading timestamps to distinguish:

```text
LIVE     recent reading
STALE    old reading
OFFLINE  no usable recent reading
```

Do not delete historical readings simply to make the live UI appear offline.

The repository contains Lab endpoint defaults that can be overridden through `.env`. Hardware/network failures should be retried gracefully rather than taking down Backend/Frontend.

### Dev1 merge rule

This clean package originates from the RTSP-only reorganisation snapshot, not from a guaranteed latest remote `Dev1` after teammate Sensor changes. When merging into team `Dev1`, preserve the newest teammate `sensor_ingest` implementation and port only the required structural/integration changes. Do not overwrite `Dev1` wholesale with this package.

## 10. Powerboard

`backend/powerboard_control/` is source-organised under Backend but runs as its own service. Frontend should preserve the teammate's switch/toggle UI and wire it to the real Powerboard service rather than replacing the UI unnecessarily.

Real credentials must not be committed.

## 11. Lighting policy — important follow-up

The newest project requirement is:

```text
read previous magenta-light state
-> ensure MAGENTA ON
-> wait for lighting to stabilise
-> capture all due cameras
-> restore the exact previous state
```

Therefore:

```text
previous ON   ON -> capture -> ON
previous OFF  OFF -> ON -> capture -> OFF
```

This matches the LeafyCV training domain and preserves the existing photoperiod state.

**Implementation status in this cleanup package:** repository cleanup intentionally does not silently rewrite runtime behaviour. The current Camera/Powerboard implementation inherited from the source ZIP still contains the older `OFF -> capture -> ON` capture sequence/watchdog logic. Reconcile that implementation with the policy above before declaring the lighting integration final or performing the final Lab smoke test.

## 12. Authentication

Backend exposes JWT endpoints:

```text
POST /api/auth/login/
POST /api/auth/refresh/
```

Camera, Sensor, and LeafyCV workers can use service credentials/tokens. Docker startup currently supports a local bootstrap service account for development. Shared/Lab environments should override development defaults in `.env`.

## 13. Frontend

Existing team pages/components should be preserved unless a change is required for integration. The main Camera/CV work belongs in Plant Vision.

Plant Vision should support:

- Camera list
- Add/Edit/Archive Camera
- RTSP configuration
- capture interval and active window
- ROI
- latest official image
- matching LeafyCV result
- analysis-pending state
- growth baseline reset where appropriate

User-facing time display may use 12-hour AM/PM while API/database times remain standard machine-readable values.

## 14. Existing AI/VLM/Growth apps

The following Backend apps are intentionally retained:

```text
accounts/
ai_agent/
vlm_agent/
farm_state/
growth/
```

They are not duplicate Camera/LeafyCV code. `growth` and `accounts` are active team functionality; AI/VLM/farm-state modules also preserve existing team work and dependencies even where some UI surfaces are not yet fully active.

## 15. Database and migrations

See `database_schema_v2.md` for the consolidated schema reference.

Do not delete old Django migrations merely because they contain superseded fields/models such as WEBCAM. Migration files describe database history and must remain intact.

## 16. Validation history

Previously recorded project validation includes:

- Camera worker tests: 12 passed
- LeafyCV test suite: 24 passed in the project environment
- `python main.py check`: Status OK
- real Lab RTSP Camera capture: passed
- CameraImage persistence: passed
- LeafyCV processing of real Lab image: passed
- ImageAnalysis persistence: passed
- duplicate analysis prevention: passed

After merging into the latest team branch, rerun tests and Docker integration checks because this cleanup package is not a substitute for the newest `Dev1` state.

## 17. Handoff rules

When integrating this repository into the team branch:

1. Use latest `Dev1` as the merge base.
2. Preserve the newest teammate Sensor implementation.
3. Keep Camera/Sensor/Powerboard as separate workers even though their source is under `backend/`.
4. Keep LeafyCV separate.
5. Preserve Camera/CV API contracts, especially `farm_level_id`.
6. Do not re-add Webcam support unless the team explicitly changes the RTSP-only decision.
7. Do not auto-seed the Lab Camera.
8. Do not rewrite working LeafyCV inference/preprocessing during repository cleanup.
9. Reconcile the lighting implementation with the MAGENTA-ON capture policy before final Lab validation.
10. Prefer unit/local/Docker testing for refactors; use the Lab for final hardware/network smoke tests.

## 18. Cleanup scope of this handoff

This clean package removes only confirmed legacy/dead/generated repository content and consolidates documentation. It intentionally does **not** redesign the runtime architecture or silently replace teammate features.

Removed items include the orphan `backend/computer_vision/` app, unused `core/api_urls.py`, unused prototype powerboard DB helper, empty Camera tools package, generated/test images, the standalone Prototype page, ineffective worker-level `.dockerignore` files, and superseded transition Markdown files.
