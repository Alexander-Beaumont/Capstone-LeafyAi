# LeafyCV1.0 - Final Growth-Area MVP

LeafyCV analyses **official images stored by the Django backend**. A separate `camera/` service owns production RTSP/webcam acquisition and uploads official JPEGs to Django. LeafyCV never opens cameras directly.

## Scope

Output fields:

- `total_canopy_coverage`
- `growth_change`
- `crowding_percentage`
- `green_percentage`
- `yellow_percentage`
- `measurement_valid`
- `processing_time_ms`

Not part of the MVP: SLOT/per-plant tracking, calibration-stick/cm measurements, MAGENTA processing, growth-stage classification, or production camera acquisition.

## Project structure

```text
LeafyCV1.0/
├── leafycv/
│   ├── __init__.py
│   ├── api.py
│   ├── metrics.py
│   ├── outputs.py
│   ├── pipeline.py
│   ├── quality.py
│   └── segmentation.py
├── tests/
├── main.py
├── requirements.txt
└── VALIDATION.md
```

## Install

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Local image validation

```bash
python main.py analyse-file --image path/to/farm_image.jpg
```

Outputs are written under `outputs/` as an annotated JPEG, mask PNG and JSON result.

## Backend contract

LeafyCV expects:

```text
GET  /api/cameras/{camera_id}/
GET  /api/cv/cameras/{camera_id}/latest-image/
GET  /api/cv/cameras/{camera_id}/latest-analysis/
GET  /api/cv/cameras/{camera_id}/latest-analysis/?valid=true
POST /api/cv/ingest/
```

`valid=true` is used only to obtain the most recent valid canopy measurement for `growth_change`. The normal latest-analysis response is used to prevent duplicate processing.

## Run once

```bash
python main.py run-once \
  --backend-base-url http://127.0.0.1:8000 \
  --camera-id 1 \
  --access-token <JWT>
```

Use `--force` only for manual testing if the latest image has already been analysed.

## Run continuously

```bash
python main.py run-loop \
  --backend-base-url http://127.0.0.1:8000 \
  --camera-id 1 \
  --poll-seconds 60 \
  --access-token <JWT>
```

The backend stores the camera capture interval and active hours; the standalone Camera service reads that configuration and creates official images. LeafyCV may poll every 60 seconds; it analyses only a new `CameraImage` ID.

For the MVP, run one LeafyCV process per camera. Automatic multi-camera discovery can be added later.
