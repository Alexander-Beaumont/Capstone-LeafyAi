# LeafyCamera FINAL LOCKED v2 - Official Capture + Shared Lighting

## Ownership

This is a standalone acquisition service. It does not import Django models and it does not run LeafyCV.

```text
Lighting/Switch <-> Camera service -> Django Backend -> CameraImage -> LeafyCV
```

The Camera service reads Camera source/schedule configuration from the Backend and uploads official JPEGs. The lighting teammate owns the actual relay/GPIO/ESP32 implementation.

## Backend APIs - unchanged

```text
GET  /api/cameras/
GET  /api/cameras/{camera_id}/
GET  /api/cv/cameras/{camera_id}/latest-image/
POST /api/cameras/{camera_id}/official-image/
```

## FINAL scheduling rule: latest official image + interval

`active_start_time` and `active_end_time` are only an eligibility window. They are not a schedule anchor.

For each Camera:

```text
enabled && cv_enabled && inside active window
    AND
(no latest official image
 OR now - latest_image.captured_at >= capture_interval_minutes)
        -> capture one image
```

Examples:

```text
latest = 10:00, interval = 30 min
10:20 -> skip
10:30 -> due
```

If the service/camera is offline from 10:00 until 12:10:

```text
12:10 -> capture ONE overdue image
next due -> 12:40
```

The service does NOT create historical backfill images for 10:30, 11:00, 11:30 or 12:00.

## New Camera and next-day alignment

A new Camera has no latest official image, so it captures on the first eligible collector poll. It can therefore be offset from older Cameras on the day it is added.

If Cameras share the same inactive overnight window and all are overdue when that window opens the next day, they are all due in the same first poll and are captured in one lighting-off batch. With typical 30/60-minute intervals and a shared 06:00-22:00 window, this usually re-aligns them each morning.

This is conditional, not guaranteed. Automatic next-day alignment does NOT apply when Cameras use different active windows, 24-hour operation, are disabled, or a Camera is not yet overdue.

## Shared capture batch

All Cameras that are due in the same collector poll share one lighting cycle:

```text
1. Lighting OFF once.
2. Wait 2 seconds.
3. Capture and JPEG-encode every due Camera while lighting remains OFF.
4. Wait 1 second after the successful capture batch.
5. Lighting ON once.
6. Upload each already-encoded JPEG.
```

This is batch synchronization. Exact same-millisecond shutter synchronization is not guaranteed and would require hardware triggering.

## Lighting/Switch contract

Preferred request:

```http
POST /api/lighting/magenta/state/
Content-Type: application/json

{"state": "OFF"}
```

Preferred response:

```json
{"success": true, "state": "OFF"}
```

Use the same endpoint with `{"state":"ON"}` after capture. If MQTT or another protocol is used, replace only `lighting_client.py` while preserving `set_state("ON"|"OFF")`.

The Lighting/Switch implementation should have its own fail-safe auto-restore/watchdog so a Camera process crash or power interruption cannot leave the grow light OFF indefinitely.

## Deployment lock

For MVP, run **one active Camera scheduler process**. Two scheduler processes can both decide that the same Camera is overdue before either uploads a new CameraImage. Active-active scheduling would require a distributed lock/idempotency design and is outside MVP.

## Failure behavior

- OFF not confirmed -> abort batch and still attempt ON.
- One Camera capture fails -> continue the other due Cameras, then restore ON.
- ON not confirmed -> treat the lighting sequence as failed; do not silently upload the batch as successful.
- Upload failure -> no new CameraImage exists; the Camera remains overdue and can retry next poll.
- LeafyCV quality FAIL is separate from Camera operational failure.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r camera\requirements.txt
python -m camera.main
```

Manual one-shot integration test:

```powershell
python -m camera.main --once --camera-id 1 --force
```

`--force` is allowed only with `--once`.

## Growth-baseline boundary

Plant replacement/rearrangement and `growth_baseline_reset_at` do **not** change Camera scheduling. The Camera service still decides capture timing only from the latest official `CameraImage`, interval, enabled flags, and active window. Baseline reset is stored by Backend and consumed by LeafyCV when calculating `growth_change`.
