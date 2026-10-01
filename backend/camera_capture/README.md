# LeafyAI Camera Capture

`backend/camera_capture` owns physical RTSP image acquisition and the technical image-quality gate used before VLM processing.

It does not diagnose plant health or decide farm actions. Those responsibilities belong to `ai_agent`.

## Runtime flow

```text
telemetry.Camera
      |
      v
RTSP / OpenCV
      |
      v
capture_fresh_frame()
      |
      v
technical quality gate
      |
      v
JPEG + quality metadata
      |
      v
telemetry.CameraImage
      |
      v
AI Agent image eligibility
      |
      v
VLM
```

Camera capture does not control grow lights. Lighting is handled independently through `powerboard_control`.

## Camera configuration

A camera record contains:

```text
farm_level
name
position
source_type = RTSP
ip_address
rtsp_port
rtsp_path
enabled
capture_interval_minutes
active_start_time
active_end_time
is_archived
```

The current bootstrap defaults in `.env.example` are:

```env
LEAFY_CAMERA_TIMEZONE=Australia/Melbourne
LEAFY_CAMERA_POLL_SECONDS=30
LEAFY_CAMERA_JPEG_QUALITY=92
LEAFY_CAMERA_WARMUP_FRAMES=12

FARM_CAMERA_USER=
FARM_CAMERA_PASSWORD=

LEAFY_CAMERA_1_NAME=Camera Level 1
LEAFY_CAMERA_1_LEVEL=1
LEAFY_CAMERA_1_IP=192.168.1.108
LEAFY_CAMERA_1_RTSP_PORT=554
LEAFY_CAMERA_1_RTSP_PATH=/stream1
LEAFY_CAMERA_1_CAPTURE_INTERVAL_MINUTES=30
LEAFY_CAMERA_1_ENABLED=true
```

The bootstrap values create/update the initial Lab camera. Additional cameras can be created and edited through the farm-scoped camera API.

Per-camera RTSP credentials can also be supplied as:

```text
CAMERA_<camera_id>_USER
CAMERA_<camera_id>_PASSWORD
```

with `FARM_CAMERA_USER` / `FARM_CAMERA_PASSWORD` as defaults.

## Scheduling

The background runtime calls `capture_due_once()` on the camera poll interval.

`capture_decision()` checks:

1. camera enabled state
2. active time window
3. whether an official image already exists
4. elapsed `capture_interval_minutes`

Missed intervals are not backfilled. One overdue camera creates at most one official capture in a collector poll.

`LEAFY_CAMERA_POLL_SECONDS` is the scheduler check interval, not the image-capture interval.

## Multi-camera behaviour

`CameraCollector.process_all()` evaluates every configured, non-archived camera.

When several cameras are due in the same poll, the collector attempts acquisition for the due cameras before persisting the completed captures. A capture/persistence failure for one camera is reported without intentionally stopping the remaining due cameras.

## Technical image-quality gate

`quality.py` evaluates whether the raw frame is technically suitable for downstream visual reasoning.

Current checks include:

```text
resolution
blur/focus
brightness
underexposure
overexposure
contrast
colour availability / monochrome-IR detection
magenta cast
```

Stored fields:

```text
quality_status
quality_flags
quality_message
quality_metrics
vlm_ready
```

Possible overall statuses are:

```text
PASS
WARN
FAIL
```

A magenta cast is represented by the `MAGENTA_CAST` warning. It does not by itself set `vlm_ready=false`.

The gate does not perform:

```text
plant disease diagnosis
plant health diagnosis
growth-stage classification
crop recommendations
farm control decisions
```

Those are downstream AI/VLM concerns.

## Persistence

`DjangoCameraRepository.upload_official_image()` stores the JPEG through the `CameraImage.path` `ImageField`.

Runtime images are stored under:

```text
backend/media/camera_images/
```

The database record also stores the capture timestamp and complete quality metadata.

`backend/media/` is runtime data and should not be committed.

## Operator API

Current farm-scoped routes:

```text
GET  /api/farms/{farm_id}/cameras/
POST /api/farms/{farm_id}/cameras/

GET   /api/farms/{farm_id}/cameras/{camera_id}/
PATCH /api/farms/{farm_id}/cameras/{camera_id}/

POST /api/farms/{farm_id}/cameras/{camera_id}/capture/

GET /api/farms/{farm_id}/camera-images/
```

Manual capture goes through the same `CameraCollector` path as scheduled capture and uses a per-camera operation lock.

Camera-image history can be filtered by camera, quality, time range, `vlm_ready` and whether an image was used by an AI recommendation run.

## Important files

```text
camera_capture/
├── tests/
│   ├── test_multi_camera_batch.py
│   ├── test_quality_gate.py
│   └── test_schedule.py
├── camera_client.py
├── camera_collector.py
├── config.py
├── quality.py
├── repository.py
└── services.py
```

Responsibilities:

- `camera_client.py`: RTSP URL construction, OpenCV acquisition and JPEG encoding.
- `camera_collector.py`: scheduling decisions, capture orchestration and upload.
- `quality.py`: deterministic technical image-quality checks.
- `repository.py`: Django ORM/file persistence boundary.
- `services.py`: constructs the Django-backed collector and exposes the runtime entry point.
- `config.py`: environment-backed capture runtime settings.

## Unit tests

From `backend/`:

```powershell
python manage.py test camera_capture
```

With Docker:

```powershell
docker compose exec backend python manage.py test camera_capture
```

These tests cover scheduling, technical quality behaviour and multi-camera collection using test doubles rather than requiring the Lab camera.

## Lab RTSP test

The default Lab RTSP URL is:

```text
rtsp://192.168.1.108:554/stream1
```

From the backend container:

```powershell
docker compose exec backend python -c "import cv2; url='rtsp://192.168.1.108:554/stream1'; cap=cv2.VideoCapture(url); ok, frame=cap.read(); print('success=', ok); print('shape=', None if frame is None else frame.shape); cap.release()"
```

A valid test should print `success=True` and a non-empty frame shape.

## Lab collector test

Force the currently configured cameras through the real collector:

```powershell
docker compose exec backend python manage.py shell -c "from camera_capture.services import build_collector; print(build_collector().process_all(force=True))"
```

Then inspect recent records:

```powershell
docker compose exec backend python manage.py shell -c "from telemetry.models import CameraImage; print(list(CameraImage.objects.order_by('-captured_at').values('id','camera_id','captured_at','quality_status','quality_flags','vlm_ready')[:10]))"
```

## Off-Lab development

The default Lab camera uses a private address, so it may be unreachable from another network.

Disable automatic physical polling when needed:

```env
LEAFY_RUNTIME_ENABLED=false
```

This prevents the Django development runtime from starting the sensor/camera/AI background workers. It does not prevent camera unit tests from running.

## VLM handoff

`ai_agent.services.latest_image_candidates()` takes the latest official image from each enabled, non-archived camera.

An image is eligible for the configured recommendation run only when it is:

- `vlm_ready=true`
- `quality_status` is `PASS` or `WARN`
- within `AIConfiguration.max_image_age_minutes`
- inside the configured `max_images` limit
- readable from storage

If at least one eligible image is readable, the recommendation run attempts the VLM path. If no reliable image is available, or the VLM path fails, the AI Agent can fall back to the sensor-only LLM path.

## Maintenance rules

When extending camera capture:

- keep RTSP acquisition separate from plant interpretation
- keep technical quality metadata with every official image
- do not make camera capture depend on changing grow-light state
- preserve per-camera scheduling and operation locks
- test multi-camera failure isolation
- keep credentials and captured media out of Git
