# LeafyAI

LeafyAI is a web-based monitoring and decision-support system for the project hydroponic farm. The current application combines farm configuration, local physical sensors, RTSP cameras, Kasa powerboards, crop/growth records and an LLM/VLM recommendation agent in one Django + React system.

This README describes the code that is currently in this repository. Historical integrations and removed experimental pipelines are intentionally not part of the runtime description.

## Current architecture

```text
React / Vite frontend
        |
        | REST + JWT
        v
Django REST backend
        |
        +--------------------+--------------------+--------------------+
        |                    |                    |                    |
        v                    v                    v                    v
 Sensor ingestion       RTSP cameras       Kasa powerboards      Growth records
        |                    |                    |                    |
        v                    v                    |                    |
 SensorReading       CameraImage + quality       |                    |
        |                    |                    |                    |
        +-----------> farm_state <---------------+--------------------+
                              |
                              v
                        AI Agent
                    LLM / VLM + safety
                              |
                 +------------+------------+
                 |                         |
                 v                         v
          advisory decisions       automatic fan/light
                                   actions after safety
```

The Django development runtime also starts background workers for sensor collection, camera capture and scheduled AI recommendations when `LEAFY_RUNTIME_ENABLED=true`.

## Main features

- User registration/login with JWT authentication.
- Create, select and delete farms.
- Automatic farm provisioning on creation:
  - one Controller `FarmDevice`
  - the seven standard sensor definitions
  - Farm Level 1 and Farm Level 2
- Per-controller sensor-ingestion configuration from the UI.
- Local HTTP sensor collection with hardware validity flags and persisted history.
- Farm dashboard and sensor history APIs.
- Per-farm RTSP camera configuration and manual/background capture.
- Technical camera image-quality gate before VLM use.
- Growth-area and plant-batch management.
- AI provider configuration per farm.
- Sensor-only LLM recommendations and camera + sensor VLM recommendations.
- Safety checks before an automated action is allowed.
- Automatic control is restricted to fan/light on-off decisions.
- Kasa powerboard status and control for the six configured logical devices.
- Recommendation/action history and input provenance.

## Technology stack

| Layer | Current technology |
| --- | --- |
| Frontend | React 19, TypeScript, Vite 8, Tailwind |
| Backend | Django 4.2, Django REST Framework |
| Authentication | Simple JWT |
| Database | SQLite for the current development deployment |
| Sensor transport | HTTP JSON |
| Camera transport | RTSP via OpenCV |
| Camera storage | Django `ImageField` under `backend/media/camera_images/` |
| Powerboard control | `python-kasa` |
| AI | OpenRouter, Ollama or mock provider |
| Configuration | `.env` / environment variables + per-farm database settings |
| Development deployment | Docker Compose |

## Repository structure

```text
Capstone-LeafyAi-main/
├── Prototype/                   UI prototype/reference material
├── backend/
│   ├── accounts/               Authentication API
│   ├── ai_agent/               LLM/VLM recommendations, safety and actions
│   ├── camera_capture/          RTSP acquisition and image-quality gate
│   ├── core/                    Django settings and URL routing
│   ├── cv/                      Migration-compatibility app; not an active analysis pipeline
│   ├── farm_state/              Normalized current farm state
│   ├── growth/                  Growing-area and plant-batch API
│   ├── leafy_runtime/           Background sensor/camera/AI workers
│   ├── powerboard_control/      Kasa powerboard integration
│   ├── sensor_ingest/           Physical HTTP sensor ingestion
│   ├── telemetry/               Core farm, camera and telemetry models/APIs
│   ├── farm_config.yaml         AI safety ranges and control policy data
│   └── manage.py
├── frontend/                    React/Vite application
├── .env.example                Development configuration template
└── docker-compose.yml
```

## Quick start with Docker

### 1. Create the local environment file

From the repository root:

```powershell
Copy-Item .env.example .env
```

Edit `.env` before starting the system. At minimum, replace placeholder secrets such as:

```env
DJANGO_SECRET_KEY=...
AI_SETTINGS_ENCRYPTION_KEY=...
OPENROUTER_API_KEY=...
```

Generate a Fernet key for `AI_SETTINGS_ENCRYPTION_KEY` with:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

The IP addresses in `.env.example` are the current LeafyAI Lab defaults and should be changed if the physical hardware changes.

### 2. Start the application

```powershell
docker compose up --build
```

The backend container automatically runs:

```text
python manage.py migrate
python manage.py bootstrap_leafy
python manage.py runserver 0.0.0.0:8000
```

Open:

```text
Frontend: http://localhost:5173
Backend:  http://localhost:8000
Admin:    http://localhost:8000/admin/
```

Create an account from the application before using authenticated farm APIs.

## Environment behaviour

Docker Compose reads the repository-root `.env` file.

For direct local backend execution outside Docker, `backend/core/settings.py` also loads `.env.example` as non-overriding development defaults. Process/environment variables still take precedence. `ai_agent/config.py` separately loads the repository-root `.env` for provider defaults.

The recommended handover/development workflow remains:

```text
.env.example
    -> copy to .env
    -> put deployment/local secrets in .env
    -> keep .env out of Git
```

Per-farm AI settings stored in the database are authoritative for normal recommendation runs.

## Farm creation and provisioning

Creating a farm through:

```text
POST /api/farms/
```

runs `provision_farm()` in the same database transaction. The backend creates:

```text
Farm
└── Controller
    ├── water_ph
    ├── electrical_conductivity
    ├── water_temperature
    ├── ambient_temperature
    ├── relative_humidity
    ├── dew_point
    ├── reservoir_water_level
    ├── Farm Level 1
    └── Farm Level 2
```

Sensor endpoints and camera details can then be configured for that farm/controller through the application.

## Sensor ingestion

The current physical sensor inputs are two HTTP JSON endpoints.

Default Lab addresses from `.env.example`:

```text
Water quality: http://192.168.1.100/readings
Ambient/level: http://192.168.1.111:8080/readings
```

The seven standard readings are:

| Sensor slug | Payload field | Hardware validity field |
| --- | --- | --- |
| `water_ph` | `ph` | `ph_valid` |
| `electrical_conductivity` | `ec` | `ec_valid` |
| `water_temperature` | `water_temperature_c` | `water_temperature_valid` |
| `ambient_temperature` | `ambient_temperature_c` | `ambient_valid` |
| `relative_humidity` | `humidity_percent` | `ambient_valid` |
| `dew_point` | `dew_point_c` | `ambient_valid` |
| `reservoir_water_level` | `water_level` | `water_level_valid` |

A collection cycle requests both configured HTTP endpoints before persistence. If either HTTP request fails or returns an invalid top-level payload, that cycle fails. When both endpoints respond, individual missing/invalid measurements are omitted and reported by the mapper; valid normalized measurements are stored as `SensorReading` rows with `source=local_http`.

See `backend/sensor_ingest/README.md` for the subsystem contract and test commands.

## Camera pipeline

Current camera flow:

```text
Camera configuration
    -> RTSP/OpenCV capture
    -> technical image-quality assessment
    -> JPEG persistence
    -> CameraImage
    -> eligible image selection
    -> VLM / AI recommendation
```

The quality gate evaluates capture suitability such as resolution, blur, exposure, contrast, colour availability and magenta cast. `MAGENTA_CAST` is a warning and does not by itself block VLM use. Plant health and crop interpretation are handled by the AI/VLM layer, not by `camera_capture`.

Default bootstrap camera values are in `.env.example`; camera records can also be managed through the farm-scoped camera API.

See `backend/camera_capture/README.md`.

## Powerboard control

The current powerboard integration uses two Kasa strips configured from environment variables:

```env
LEAFY_POWERBOARD_1_IP=192.168.1.102
LEAFY_POWERBOARD_2_IP=192.168.1.101
```

Current logical device mapping:

| ID | Device | Board | Child |
| ---: | --- | --- | ---: |
| 1 | pH Doser | board 1 | 0 |
| 2 | EC Doser | board 1 | 1 |
| 3 | Irrigation Pump | board 1 | 2 |
| 4 | Farm Fan | board 2 | 0 |
| 5 | Light Level 1 | board 2 | 1 |
| 6 | Light Level 2 | board 2 | 2 |

The operator API is:

```text
GET  /api/devices/
POST /api/devices/{device_id}/state/
```

The Kasa bridge confirms physical state before returning a successful state change.

## Farm state

`/api/farm-state/{farm_id}/` is the normalized read model used by the application and AI agent. It is assembled from persisted database records and does not directly poll hardware.

It includes the current sensor state, freshness/quality information, sensor trend summaries, farm levels, growing areas/current batches, cameras and any persisted actuator/setpoint/tank observations.

## AI Agent

The AI Agent stores configuration per farm and supports manual or scheduled recommendation runs.

Current input flow:

```text
farm_state
+ latest fresh non-suspect sensor readings
+ latest technically eligible camera image(s)
        |
        +-- images available --> VLM
        |
        +-- no usable image / VLM failure --> sensor-only LLM fallback
        |
        v
strict JSON parsing
        |
        v
SafetyCheck
        |
        +-- advisory targets --> notification only
        |
        +-- fan/light + safety passed --> Kasa action
```

Only `fans` and `light` with an explicit `on`/`off` state are classified as automated. Irrigation pump, nutrient dosing, pH dosing, harvest and other recommendations remain notification-only.

Every run records its source sensor readings, selected camera images, visual evidence, freshness summary, provider/model, fallback information, recommendations, safety checks and hardware actions.

## Growth management

The growth API manages:

```text
Farm
 -> Farm Level
    -> Growing Area
       -> Batch Placement
          -> Plant Batch
```

The application supports creating/updating growing areas, creating batches, moving a batch between areas, and marking a batch as harvested or terminated.

Physical plant movement remains a human operation; the database movement records the placement state after the operator performs the move.

## Important API groups

| Area | Main endpoints |
| --- | --- |
| Authentication | `/api/auth/login/`, `/api/auth/refresh/`, `/api/auth/register/` |
| Farms | `/api/farms/` |
| Farm dashboard | `/api/farms/{farm_id}/dashboard/` |
| Farm state | `/api/farm-state/{farm_id}/` |
| Sensor config | `/api/farms/{farm_id}/sensor-ingest/` |
| Sensor readings/history | `/api/farms/{farm_id}/sensor-readings/`, `/api/farms/{farm_id}/sensor-history/` |
| Cameras | `/api/farms/{farm_id}/cameras/` |
| Camera images | `/api/farms/{farm_id}/camera-images/` |
| Growth | `/api/growing-areas`, `/api/batches`, `/api/move-batch`, `/api/create-batch` |
| AI settings/runs | `/api/ai-agent/farms/{farm_id}/...` |
| Powerboards | `/api/devices/`, `/api/devices/{device_id}/state/` |

Most application APIs require a JWT access token.

## Background runtime

When Django is started with `runserver` and:

```env
LEAFY_RUNTIME_ENABLED=true
```

`leafy_runtime` starts daemon workers for:

- due sensor collections
- due camera captures
- due AI recommendation schedules

The workers are not started by commands such as `migrate`, `test`, `shell` or `collect_sensors`.

Disable physical background activity during off-Lab development when required:

```env
LEAFY_RUNTIME_ENABLED=false
```

AI scheduling can also be disabled independently:

```env
LEAFY_AI_SCHEDULER_ENABLED=false
```

## Testing

### Backend

From the running Docker stack:

```powershell
docker compose exec backend python manage.py check
docker compose exec backend python manage.py test
```

Focused suites:

```powershell
docker compose exec backend python manage.py test sensor_ingest
docker compose exec backend python manage.py test camera_capture
docker compose exec backend python manage.py test ai_agent
docker compose exec backend python manage.py test farm_state
docker compose exec backend python manage.py test telemetry
docker compose exec backend python manage.py test growth
```

### Frontend

```powershell
docker compose exec frontend npm test -- --run
docker compose exec frontend npm run build
docker compose exec frontend npm run lint
```

### Lab sensor smoke test

```powershell
docker compose exec backend python manage.py collect_sensors --once
```

### Lab camera smoke test

```powershell
docker compose exec backend python manage.py shell -c "from camera_capture.services import build_collector; print(build_collector().process_all(force=True))"
```

### Lab powerboard smoke test

The active runtime path can be checked through the API:

```text
GET /api/devices/
```

or from the Django shell:

```python
from powerboard_control.bridge import get_powerboard_bridge
print(get_powerboard_bridge().get_all_device_statuses())
```

Hardware smoke tests require connection to the LeafyAI Lab network.

## Runtime-generated files

The following are local/runtime artifacts and are ignored by Git:

```text
.env
backend/db.sqlite3
backend/media/
__pycache__/
*.pyc
```

Do not place real passwords, API keys or camera credentials in tracked documentation or `.env.example`.

## Source-code documentation

Comments in the current source focus on subsystem boundaries, safety rules, concurrency, persistence and other non-obvious behaviour. They intentionally avoid restating self-explanatory code.

The module READMEs provide additional detail for:

- `backend/sensor_ingest`
- `backend/camera_capture`
- `frontend`

## Handover notes

- `Prototype/` is retained as project design/reference material; it is not the production frontend.
- `backend/cv/` remains installed for migration compatibility and is not the active plant-analysis pipeline.
- Physical hardware IPs in `.env.example` are Lab defaults, not public addresses.
- Camera capture performs technical image checks; plant interpretation is performed downstream by the VLM/AI Agent.
- Current automated AI hardware control is limited to fan/light actions that pass the safety layer.
