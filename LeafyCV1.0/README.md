# LeafyCV1.0 FINAL LOCKED v2.1 - Semantic Canopy + Quality Gate + Baseline-Safe Growth

## Purpose

LeafyCV analyses Backend-owned official `CameraImage` records. It never opens RTSP/webcam streams and never controls lighting.

```text
Camera -> Backend -> CameraImage -> LeafyCV -> ImageAnalysis -> Backend
```

## Final model

```text
Architecture: U-Net
Encoder: EfficientNet-B0
Input: RGB 512 x 512
Preprocessing: BGR -> RGB -> resize -> float32 / 255.0
Output: sigmoid probability -> threshold 0.5 -> binary mask 0/255
```

The model checkpoint is bundled at:

```text
models/leafy_canopy_effnet_b0_final.pth
```

## Processing chain

For the newest official image returned for each Camera, when that image has not already been analysed:

```text
Camera-specific ROI
-> deterministic image-quality gate
-> U-Net + EfficientNet-B0 canopy segmentation
-> binary canopy mask
-> canopy / crowding / colour metrics
-> growth_change vs the same Camera's previous valid analysis
   only inside the current growth baseline
-> JSON POST /api/cv/ingest/
```

Quality failures set:

```text
measurement_valid = false
vlm_ready = false
quality_status = FAIL
quality_flags = [...]
quality_message = deterministic warning
```


## Growth baseline reset - plant/layout changes

`growth_change` is relative **visible canopy coverage change** between valid observations inside the same Camera baseline. It is **not normalized by elapsed time** and is not an exact biological growth rate for individual plants. LeafyCV does not track plant IDs.

Backend exposes the nullable Camera field:

```text
growth_baseline_reset_at
```

When plants are moved, added, removed, replaced, transferred between Cameras, or the physical view/ROI is materially changed, the affected Camera baseline must be reset. For a transfer Camera 1 -> Camera 2, reset **both** Cameras.

LeafyCV behavior:

```text
latest valid analysis captured before reset -> ignore for growth
first valid image after reset              -> growth_change = null
next valid image                           -> compare with first post-reset image
```

Historical `CameraImage` and `ImageAnalysis` rows are never edited or deleted. The semantic U-Net model and its checkpoint do not change. Only the temporal comparison logic is reset.

The Backend endpoint paths remain unchanged; the reset timestamp is part of the existing Camera GET/PATCH contract.

## Latest-only processing - MVP

LeafyCV intentionally uses the Backend `latest-image` endpoint rather than a historical pending-image queue.

```text
newest official CameraImage has no matching analysis -> analyse it
newest official CameraImage is already analysed     -> skip
LeafyCV was offline across multiple captures        -> analyse the newest available image only
older unanalysed CameraImages                       -> no historical backfill in MVP
```

This means `growth_change` compares two valid observations that may be separated by more than one capture interval. It remains a relative canopy change, not a per-hour or per-day growth rate.

## Multi-camera behavior

LeafyCV can process one Camera or all enabled/CV-enabled Cameras in one process.

All active Cameras:

```powershell
python main.py run-loop --backend-base-url http://127.0.0.1:8000
```

One Camera only:

```powershell
python main.py run-loop --camera-id 1 --backend-base-url http://127.0.0.1:8000
```

Each Camera is independent:

- duplicate detection uses that Camera's latest analysis;
- `growth_change` uses that Camera's previous valid canopy only;
- ROI comes from that Camera's configuration;
- `camera_id` and `image_id` are preserved in every ingest request.

Camera capture synchronization is handled by the Camera service. LeafyCV does not need to analyse synchronized images at exactly the same instant; it processes each Camera's newest available official image independently and reuses one loaded semantic model.

## Backend APIs

```text
GET  /api/cameras/
GET  /api/cameras/{camera_id}/
GET  /api/cv/cameras/{camera_id}/latest-image/
GET  /api/cv/cameras/{camera_id}/latest-analysis/
GET  /api/cv/cameras/{camera_id}/latest-analysis/?valid=true
POST /api/cv/ingest/
```

## Quick checks

```powershell
pip install -r requirements.txt
python main.py check
pytest -q
```

Analyse one local image:

```powershell
python main.py analyse-file --image path\to\farm.jpg
```


## Camera scheduling boundary

LeafyCV does not decide capture timing. The Camera service uses each Camera's latest official CameraImage timestamp plus `capture_interval_minutes`, subject to the active time window. Missed captures are not backfilled. This scheduling rule does not change any LeafyCV endpoint.

## Operational failure vs quality failure

A quality FAIL is a successfully decoded/processed image that is technically unsuitable for trusted CV/VLM use. A model load error, Backend outage, image download failure, or inference exception is an operational failure: LeafyCV logs it and creates no ImageAnalysis. A later poll retries that same image only if it is still the newest unanalysed image; if newer official images have arrived, older unanalysed images are not backfilled. It must not fabricate `quality_status=FAIL` for a job that never completed.
