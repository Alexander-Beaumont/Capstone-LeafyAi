# Integration Manifest

## KEEP from team repo

- Existing Backend project/apps, authentication, AI Agent, VLM Agent, farm-state and growth modules.
- Existing Frontend router/layout/pages including AI Agent, History, Growth & Harvesting, Settings.
- Existing Camera scheduler/capture orchestration and LeafyCV semantic model pipeline.
- Existing team database schema/migrations through telemetry `0009`.

## ADD

- `backend/telemetry/migrations/0010_camera_is_archived.py`
- `backend/telemetry/management/commands/seed_base.py` — non-camera bootstrap only.
- Camera / LeafyCV / Sensors / Powerboard Docker files.
- Docker named volumes for SQLite/media persistence; no `runtime/` directory is shipped.
- Expanded `.env.example`.
- Docker Compose `vision` and `hardware` profiles.

## CHANGE

- Camera serializer: FINAL LOCKED writable `farm_level_id` primary-key API field (mapped internally to Django `farm_level`), source/window/ROI validation, archive field.
- Camera view: active list excludes archived, hard delete disabled.
- CameraImage and ImageAnalysis generic APIs are read-only.
- Official JPEG and CV ingest validation are final-contract behavior.
- Plant Vision is fully implemented while all other team pages remain.
- Camera RTSP URL builder requires explicit Backend port/path instead of hidden stream defaults.
- API service layer parses an HTTP body once and supports Camera/CV/Sensor/Powerboard calls.

## REMOVE FROM THE DISTRIBUTED FULL PACKAGE

- Tracked `.env`.
- Tracked local `backend/db.sqlite3`.
- Frontend local `.env`.
- Any runtime/generated output.

These removals guarantee a fresh repository does not contain the earlier Test Camera or a preconfigured Lab Camera.
