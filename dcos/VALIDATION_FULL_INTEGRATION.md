# Validation performed for this package

- `camera/tests`: **12 passed** in the build environment.
- Python syntax compilation (`backend`, `camera`, `LeafyCV1.0`, `Sensors`, `Powerboard`): **PASS**.
- Camera API regression test added: POST/response use FINAL LOCKED `farm_level_id`; legacy public `farm_level` is not exposed by CameraSerializer.
- Plant Vision Camera types/forms/payloads use `farm_level_id` consistently with the FINAL LOCKED Camera API contract. Rerun `npm run build` after extraction as part of local validation.
- LeafyCV tests in the build environment: **23 passed, 1 skipped** because `segmentation_models_pytorch` is not installed in this isolated artifact environment. The repository still pins `segmentation-models-pytorch==0.5.0`; in the user's project venv the same LeafyCV suite was already run with **24 passed** and `python main.py check` returned `Status: OK`.
- Hardcoded old Camera `192.168.1.106`: **not present in executable/config source**.
- Distributed `.env`, `frontend/.env`, tracked local `backend/db.sqlite3`, local venvs/node_modules/runtime output: **removed/ignored**.

A final local Django migration/API test should still be run after extracting, because this artifact environment cannot install Django packages from the internet.

## Schema-lock correction validation (2026-09-12)

- `camera/tests`: **12 passed** after restoring the locked API name.
- Python source compile check: **PASS** before packaging.
- Static contract audit: Plant Vision Camera type, create form, edit form, POST/PATCH payloads and CameraSerializer all use public `farm_level_id`.
- Django model relation remains `farm_level`; **no database migration** is required for this API-name correction.
- Backend Django API tests were not executed in the artifact container because Django is not installed in that container; run the included regression test in the project/backend venv or Docker.
- Frontend build should be rerun in the project environment (`npm ci && npm run build`); an artifact-container dependency install was incomplete, so no build result is claimed here.
