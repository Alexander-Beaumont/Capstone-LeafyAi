# LeafyAI — Final Database Schema and Data-Flow Reference

**Release alignment:** LeafyAI final main-branch snapshot, 7 October 2026.  
**Database:** Django ORM with SQLite for the development/laboratory deployment.  
**Purpose:** Maintainer-facing description of the *implemented* persisted models, relationships, constraints, data provenance and configuration authority. This document supersedes the earlier ThingSpeak-oriented schema proposal; it is not a request to create new database tables.

> **Sources of truth:** `backend/telemetry/models.py`, `backend/sensor_ingest/models.py`, `backend/powerboard_control/models.py`, `backend/ai_agent/models.py`, their committed migrations, and the corresponding runtime services. Consult `python manage.py showmigrations` and `sqlmigrate` for the exact database DDL in a given deployment. All model fields listed below are current source-code fields, not proposed ones.

## Contents

1. [Runtime scope and entity map](#1-runtime-scope-and-entity-map)
2. [Farm structure and crop records](#2-farm-structure-and-crop-records)
3. [Sensors, normalization and telemetry](#3-sensors-normalization-and-telemetry)
4. [RTSP cameras and image-quality evidence](#4-rtsp-cameras-and-image-quality-evidence)
5. [Farm-scoped runtime configuration](#5-farm-scoped-runtime-configuration)
6. [AI recommendations, safety and action audit](#6-ai-recommendations-safety-and-action-audit)
7. [Retained supporting/reference models](#7-retained-supportingreference-models)
8. [Key constraints, deletion and migration compatibility](#8-key-constraints-deletion-and-migration-compatibility)
9. [Configuration ownership and operational flows](#9-configuration-ownership-and-operational-flows)
10. [Verification, change procedure and limitations](#10-verification-change-procedure-and-limitations)

## 1. Runtime scope and entity map

The final application is **React/TypeScript/Vite → Django/DRF → SQLite**. Django owns local-HTTP sensor polling, RTSP/JPEG capture, deterministic technical image-quality assessment, AI orchestration, safety policy and TP-Link/Kasa bridge operations. Docker Compose starts **backend** and **frontend** only. The legacy `cv` Django app is retained for historical migration compatibility; no active LeafyCV segmentation/plant-health model is used.

```text
Farm
 ├── FarmDevice (new farm provisioned with one Controller)
 │    ├── FarmLevel (Top=1, Bottom=2)
 │    │    ├── GrowingArea ── BatchPlacement ── PlantBatch
 │    │    └── Camera ── CameraImage ─┐
 │    ├── Sensor ── SensorReading ────┤ evidence M:N
 │    └── SensorIngestConfiguration   │
 ├── PowerboardConfiguration         │
 ├── AIConfiguration                  │
 └── AIRecommendationRun <───────────┘
      └── AIDecision
           ├── SafetyCheck (0..1 per decision)
           └── FarmAction (0..many; attempted automatic hardware execution)
```

Farm ownership is established directly for FarmDevice, PowerboardConfiguration, AIConfiguration and AIRecommendationRun; child entities reach a farm through their parent relationships. **Physical strip outlets are not ORM rows**: six logical device IDs are constants in `backend/powerboard_control/config.py`.

### Schema conventions

- Unless stated otherwise, Django supplies an implicit `id` primary key on each model; physical SQLite column names use Django's defaults (`<foreign_key_field>_id` for foreign keys). The primary key for `BatchPlacement` is **`id`**, not a composite `(batch, area)` key.
- `FK` means `ForeignKey`; `O2O` means `OneToOneField` (unique foreign key); `M2M` is an automatically managed association/join table. `CASCADE` and `PROTECT` refer to Django deletion policies.
- `blank=True`, form/API validation and Django field `choices` do not automatically imply a database `CHECK` constraint. Explicit database constraints are separately identified below.
- `DateTimeField(auto_now_add=True)` records row creation and `auto_now=True` updates a timestamp on ordinary model saves; these are Django behaviors, not a claim about a database-side trigger/default.
- Migrations, not this Markdown file, determine the executable SQLite schema. The descriptions of field types use Django names so they remain unambiguous across database engines.

### Current persisted-model inventory

| App / ORM table prefix | Current models | Purpose |
|---|---|---|
| `telemetry_` | Farm, FarmDevice, FarmLevel, GrowingArea, PlantBatch, BatchPlacement | Farm topology and crop management |
| `telemetry_` | Sensor, SensorReading, Camera, CameraImage | Source telemetry and official visual evidence |
| `telemetry_` | NutrientTank, Doser, SafeRange, ActuatorStateObservation, SetpointObservation | Retained supporting/reference objects, not active ThingSpeak ingestion |
| `sensor_ingest_` | SensorIngestConfiguration | Per-controller local-HTTP ingestion configuration and health |
| `powerboard_control_` | PowerboardConfiguration | Per-farm physical Kasa strip addresses |
| `ai_agent_` | AIConfiguration, AIRecommendationRun, AIDecision, SafetyCheck, FarmAction | AI configuration and auditable decision/safety/action chain |

Django's own installed framework/auth/session tables are not reproduced here. The `growth` and `farm_state` application modules use the persisted telemetry models rather than declaring additional current models.

## 2. Farm structure and crop records

### `telemetry.Farm` — `telemetry_farm`

| Field | Django type / rule | Role |
|---|---|---|
| `id` | implicit PK | Farm identifier |
| `name` | `CharField(255)` | Human-readable farm name |
| `location` | `CharField(255, blank=True, null=True)` | Optional farm location |

A farm is the logical ownership scope for configurations and AI history. Farm creation via `telemetry.views.FarmViewSet.perform_create()` and `telemetry.farm_provisioning.provision_farm()` is atomic: it provisions one Controller FarmDevice, seven standard Sensor definitions, and levels 1/2. This is the **application provisioning contract**, not a constraint that every arbitrary Farm row must already contain these children.

### `telemetry.FarmDevice` — `telemetry_farmdevice`

| Field | Django type / rule | Role |
|---|---|---|
| `farm` | FK → Farm, `CASCADE` | Owning farm |
| `name` | `CharField(255)` | Controller/device name |
| `slug` | `SlugField(80, unique=True, blank=True)` | Globally unique stable identifier, generated if omitted |
| `device_type` | `CharField(100, blank=True, null=True)` | Hardware/controller type |

`Farm 1—N FarmDevice`. The final new-farm flow creates a device named `Controller`, with type `controller`.

### `telemetry.FarmLevel` — `telemetry_farmlevel`

| Field | Django type / rule | Role |
|---|---|---|
| `device` | FK → FarmDevice, `CASCADE` | Owning controller |
| `level_number` | `IntegerField`, choices 1=Top/2=Bottom | Physical rack level |

Two explicit database constraints apply: `level_number_must_be_1_or_2` (`CHECK level_number IN (1,2)`), and `unique_level_per_device` (unique `device, level_number`). A newly provisioned controller gets levels 1 and 2.

### `telemetry.GrowingArea` — `telemetry_growingarea`

| Field | Django type / rule | Role |
|---|---|---|
| `farm_level` | FK → FarmLevel, `CASCADE` | Physical level |
| `name` | `CharField(255)` | Area label |
| `slot_count` | `IntegerField` | Declared capacity |

The growth API enforces relevant farm/level/slot validation. The model itself does not hard-code three mandatory areas or fixed physical slot layouts.

### `telemetry.PlantBatch` — `telemetry_plantbatch`

| Field | Django type / rule | Role |
|---|---|---|
| `plant_type` | `CharField(100)` | Crop type |
| `planting_date` | `DateField` | Planting date |
| `growth_stage` | `CharField(50)`, choices `seedling`, `early_growth`, `mature` | Growth-stage label |
| `status` | `CharField(50)`, choices `active`, `harvested`, `failed` | Batch lifecycle |

Growth stage and status are user/application-controlled records; **the VLM does not automatically and reliably assign exact growth stage or harvest date** in the final system.

### `telemetry.BatchPlacement` — `telemetry_batchplacement`

| Field | Django type / rule | Role |
|---|---|---|
| `plant_batch` | FK → PlantBatch, `CASCADE` | Cohort being placed |
| `growing_area` | FK → GrowingArea, `CASCADE` | Destination area |
| `start_date` | `DateTimeField` | Placement start |
| `end_date` | `DateTimeField(blank=True, null=True)` | Placement end; null for active |

`PlantBatch 1—N BatchPlacement` and `GrowingArea 1—N BatchPlacement`. The model has an implicit single-column `id` PK; it **does not** declare a composite primary key or a current DB-level unique active-placement constraint. Growth services apply farm isolation and move/harvest business rules, including closing previous placement records.

## 3. Sensors, normalization and telemetry

**Final source:** two farm/controller-configured local HTTP JSON endpoints. **Not in current runtime:** ThingSpeak channels, ThingSpeak field1–field8 mappings, ThingSpeak backfill, ThingSpeak entry-ID deduplication workers, or active `IngestionSourceState`/`IngestionRecord` models. Migration `sensor_ingest/0002_remove_legacy_ingestion_audit.py` explicitly removes those last two legacy models.

```text
SensorIngestConfiguration (per FarmDevice)
      ├─ water_quality_url ── GET JSON ──┐
      └─ ambient_sensor_url ─ GET JSON ──┤
                                         v
                       sensor_ingest.services.mapper
                            7 canonical slugs
                                         v
                                SensorReading
                              /       |       \
                      Farm Overview  History  AI input evidence
```

### Canonical seven-sensor mapping

The authoritative mapping is `backend/sensor_ingest/services/mapper.py` (`SENSOR_DEFINITIONS`), not a proposed ThingSpeak mapping.

| `Sensor.slug` | `sensor_type` | HTTP source | JSON value key | JSON validity key | Unit |
|---|---|---|---|---|---|
| `water_ph` | `ph` | `water_quality` | `ph` | `ph_valid` | `pH` |
| `electrical_conductivity` | `ec` | `water_quality` | `ec` | `ec_valid` | `uS/cm` |
| `water_temperature` | `water_temperature` | `water_quality` | `water_temperature_c` | `water_temperature_valid` | `°C` |
| `ambient_temperature` | `ambient_temperature` | `ambient` | `ambient_temperature_c` | `ambient_valid` | `°C` |
| `relative_humidity` | `humidity` | `ambient` | `humidity_percent` | `ambient_valid` | `%` |
| `dew_point` | `dew_point` | `ambient` | `dew_point_c` | `ambient_valid` | `°C` |
| `reservoir_water_level` | `water_level` | `ambient` | `water_level` | `water_level_valid` | `cm` |

The hardware validity key must literally be `true` for an individual value to be used. Missing, nonnumeric, nonfinite and explicitly invalid measurements are omitted. Basic physically implausible numbers (for example pH outside 0–14, humidity outside 0–100%, or negative EC/level) are retained as `suspect` rather than silently relabelled valid. Crop safety recommendations are evaluated in a separate layer.

### `telemetry.Sensor` — `telemetry_sensor`

| Field | Django type / rule | Role |
|---|---|---|
| `device` | FK → FarmDevice, `CASCADE`, related name `sensors` | Source controller |
| `slug` | `SlugField(80, blank=True)` | Stable device-local integration key |
| `sensor_type` | `CharField(50)` | Normalized farm-state/AI type |
| `unit` | `CharField(50)` | Display unit |
| `enabled` | `BooleanField(default=True)` | Reading acceptance/collection setting |
| `expected_interval_seconds` | nullable `PositiveIntegerField` | Expected cadence |
| `stale_after_seconds` | nullable `PositiveIntegerField` | Freshness threshold |

Database uniqueness: `unique_sensor_slug_per_device` (`device, slug`). `seed_sensors`/`ensure_sensor_definitions` create or reconcile the canonical sensor definitions.

### `telemetry.SensorReading` — `telemetry_sensorreading`

| Field | Django type / rule | Role |
|---|---|---|
| `sensor` | FK → Sensor, `PROTECT`, related name `readings` | Measured sensor |
| `value` | `DecimalField(max_digits=12, decimal_places=4)` | Normalized observation |
| `measured_at` | `DateTimeField(default=timezone.now, db_index=True)` | Observation timestamp |
| `received_at` | `DateTimeField(auto_now_add=True)` | Database receipt/creation time |
| `source` | `CharField(50, default="manual")` | Current collector stores **`local_http`** |
| `source_channel_id` | `CharField(100, blank=True, default="")` | Current collector records `water_quality` or `ambient` |
| `source_entry_id` | nullable `PositiveBigIntegerField` | Legacy/general external-entry identifier; **current local-HTTP collector stores NULL** |
| `quality_status` | `CharField(20)`, choices `valid`, `unverified`, `suspect`; default `unverified` | Measurement validity indicator |
| `quality_notes` | `CharField(255, blank=True, default="")` | Diagnostic message |

**Timestamp precision:** in the **current** `SensorCollector.collect()` implementation, `measured_at = timezone.now()` is assigned at the collection cycle, not copied from a source JSON measurement timestamp. `received_at` is assigned on row creation. These may be close but have different semantics. Do not describe the active local-HTTP path as preserving an original hardware measurement timestamp that the collector does not read.

Indexes/constraints:

- `measured_at` indexed; composite index `sensor_measured_idx` on (`sensor`, `measured_at`).
- Retained uniqueness definition `unique_external_sensor_reading` on (`sensor`, `source`, `source_channel_id`, `source_entry_id`). It is **not** an active ThingSpeak deduplication pipeline; current HTTP rows have `source_entry_id=NULL`. In SQLite, `NULL` values in such a composite unique constraint do not ensure distinct local-HTTP collection cycles.
- History is append-oriented and exposed read-only through the normal operator APIs. A collection cycle fetches both endpoints before persisting readings; if either endpoint raises a transport/payload error, that cycle stores no new readings. Valid/missing/invalid per-value behavior is handled by the mapper.

### `sensor_ingest.SensorIngestConfiguration` — `sensor_ingest_sensoringestconfiguration`

| Field | Django type / rule | Role |
|---|---|---|
| `device` | O2O → FarmDevice, `CASCADE`, related name `sensor_ingest_configuration` | One configuration per controller |
| `enabled` | `BooleanField(default=True)` | Enables configured collection |
| `water_quality_url` | `URLField(500, blank=True, default="")` | Water-quality HTTP JSON URL |
| `ambient_sensor_url` | `URLField(500, blank=True, default="")` | Ambient/level HTTP JSON URL |
| `poll_interval_seconds` | `PositiveIntegerField(default=30)`, validator 1–86400 | Scheduler polling |
| `sensor_stale_threshold_seconds` | `PositiveIntegerField(default=120)`, validator 1–604800 | Sensor staleness interval |
| `last_attempt_at` | nullable `DateTimeField` | Ingestion attempt time |
| `last_success_at` | nullable `DateTimeField` | Last successful cycle |
| `last_error` | `TextField(blank=True, default="")` | Last reported failure |
| `consecutive_failures` | `PositiveIntegerField(default=0)` | Health/backoff state |
| `updated_at` | `DateTimeField(auto_now=True)` | Configuration update |

Rows are ordered by `device_id` by default. `sensor_ingest.signals.ensure_ingest_configuration` creates a configuration on a newly created FarmDevice. A non-bootstrap farm starts with blank endpoint URLs and ingestion disabled until configured; the designated Lab device can receive environment bootstrap defaults. Once a row exists, UI/API configuration is authoritative and repeated bootstrap does not overwrite it.

Operator endpoints: `GET/PATCH /api/farms/{farm_id}/sensor-ingest/{device_id}/`; `POST .../test/` (fetch/validate, no persistence); `POST .../collect/` (persist). See `sensor_ingest/views.py` and its README for locking, validation, errors and precise responses.

## 4. RTSP cameras and image-quality evidence

### `telemetry.Camera` — `telemetry_camera`

| Field | Django type / rule | Role |
|---|---|---|
| `farm_level` | FK → FarmLevel, `CASCADE` | Monitored level |
| `name` | `CharField(255)` | Camera label |
| `position` | nullable/blank `CharField(100)` | Optional descriptive position |
| `source_type` | `CharField(20)`, available choice `RTSP` | Final supported camera source |
| `ip_address` | nullable/blank `GenericIPAddressField` | Camera IP |
| `rtsp_port` | nullable/blank `IntegerField` | RTSP port |
| `rtsp_path` | nullable/blank `CharField(255)` | RTSP stream path |
| `enabled` | `BooleanField(default=True)` | Capture enablement |
| `capture_interval_minutes` | `PositiveIntegerField(default=30)` | Scheduled capture interval |
| `active_start_time`, `active_end_time` | nullable/blank `TimeField` | Active capture window |
| `is_archived` | `BooleanField(default=False)` | Operator soft-delete/archival flag |

Current runtime supports RTSP capture only. The operator-facing camera delete flow archives; the API does not expose hard delete. A bootstrap-configured named Lab camera can be updated from `LEAFY_CAMERA_1_*` settings, so camera bootstrap has **different update behavior** from sensor/powerboard `get_or_create` configuration.

### `telemetry.CameraImage` — `telemetry_cameraimage`

| Field | Django type / rule | Role |
|---|---|---|
| `camera` | FK → Camera, `PROTECT` | Source camera |
| `captured_at` | `DateTimeField` | Successful capture timestamp |
| `path` | `ImageField(upload_to="camera_images/")` | Stored JPEG / relative media path |
| `vlm_ready` | `BooleanField(default=False)` | Visual-input eligibility |
| `quality_status` | `CharField(16, default="UNKNOWN")` | Technical status, normally `PASS` / `WARN` / `FAIL` |
| `quality_flags` | `JSONField(default=list)` | Technical quality conditions |
| `quality_message` | `TextField(default="")` | Human-readable diagnostic |
| `quality_metrics` | `JSONField(default=dict)` | Resolution/exposure/focus/colour metrics |

Captured images are **files under configured `MEDIA_ROOT` plus database metadata**, not image blobs stored in SQLite. Technical image quality is not a basil health diagnosis. For the final quality policy, PASS/WARN can be VLM-ready; FAIL images may remain in history but are excluded from visual input. Magenta grow-light cast is treated as a warning rather than by itself blocking VLM use. The VLM performs qualitative plant interpretation; there is no active per-plant CV measurement table or LeafyCV runtime.

`FarmLevel 1—N Camera 1—N CameraImage`; each AIRecommendationRun may reference 0..many CameraImages via a separate M2M association table.

## 5. Farm-scoped runtime configuration

### `powerboard_control.PowerboardConfiguration` — `powerboard_control_powerboardconfiguration`

| Field | Django type / rule | Role |
|---|---|---|
| `farm` | O2O → Farm, `CASCADE`, related name `powerboard_configuration` | One farm-specific configuration row |
| `powerboard_1_ip` | nullable/blank `GenericIPAddressField` | Kasa strip 1 IP |
| `powerboard_2_ip` | nullable/blank `GenericIPAddressField` | Kasa strip 2 IP |
| `updated_at` | `DateTimeField(auto_now=True)` | Saved configuration timestamp |

The first Lab farm is seeded *once* by `bootstrap_leafy` using `LEAFY_POWERBOARD_1_IP` and `LEAFY_POWERBOARD_2_IP` if its configuration does not yet exist. Later UI PATCH operations change the database row directly. A new farm does **not** silently inherit the Lab strip addresses; unconfigured farm-scoped control must fail safely. Environment addresses remain a legacy fallback only for explicitly non-farm-scoped bridge calls.

Logical outlet mapping in `powerboard_control/config.py` is code, **not** data stored in `PowerboardConfiguration`:

| Logical ID | Target | Board | Kasa `child_index` | Auto-AI scope |
|---:|---|---|---:|---|
| 1 | pH Doser | `board_1` | 0 | Advisory only |
| 2 | EC Doser | `board_1` | 1 | Advisory only |
| 3 | Irrigation Pump | `board_1` | 2 | Advisory only |
| 4 | Farm Fan | `board_2` | 0 | Eligible after safety check |
| 5 | Light Level 1 | `board_2` | 1 | Eligible as part of grouped lights |
| 6 | Light Level 2 | `board_2` | 2 | Eligible as part of grouped lights |

The API is `GET/PATCH /api/farms/{farm_id}/powerboard-config/`; `GET /api/devices/?farm_id=...`; `POST /api/devices/{device_id}/state/` with `farm_id` for farm-specific control. The frontend changes physical addresses but **does not edit `.env`** and does not remap the logical outlets.

### `ai_agent.AIConfiguration` — `ai_agent_aiconfiguration`

| Field | Django type / rule | Role |
|---|---|---|
| `farm` | O2O → Farm, `CASCADE`, related name `ai_configuration` | Farm-specific settings |
| `llm_provider`, `vlm_provider` | `CharField(20)`, choices `openrouter`, `ollama`, `mock`; default `mock` | AI backends |
| `llm_model`, `vlm_model` | `CharField(255)`; default `mock-llm`/`mock-vlm` | Model identifiers |
| `llm_api_key_encrypted`, `vlm_api_key_encrypted` | `TextField(blank=True, default="")` | Encrypted provider credentials |
| `schedule_enabled` | `BooleanField(default=False)` | Scheduled recommendations toggle |
| `timezone` | `CharField(64, default="Australia/Melbourne")` | Schedule timezone |
| `interval_minutes` | `PositiveIntegerField(default=30)`, validator 1–1440 | Scheduled interval |
| `active_start_time`, `active_end_time` | `TimeField`, defaults 08:00 / 20:00 | Active AI window |
| `max_images` | `PositiveSmallIntegerField(default=4)`, validator 1–8 | Image selection limit |
| `max_image_age_minutes` | `PositiveIntegerField(default=60)`, validator 1–10080 | Image age limit |
| `updated_at` | `DateTimeField(auto_now=True)` | Settings update |

Credentials are encrypted by application code and masked in API responses; their encryption key must be backed up separately via secure deployment configuration. A farm's AIConfiguration is the runtime source for providers, models and scheduling after it has been created.

## 6. AI recommendations, safety and action audit

```text
Latest eligible SensorReading(s)
       +
PASS/WARN, vlm_ready, age-qualified CameraImage(s)
       |
       v
AIRecommendationRun (manual or scheduled)
  ├─ VLM with sensor+image evidence, when possible
  └─ sensor-only LLM fallback when image/VLM is unusable
       |
       v
AIDecision (one row per structured recommendation)
       |
       v
SafetyCheck (deterministic application-side checks)
       |
       +── unsupported/risky target: advisory; no automatic FarmAction
       └── permitted fan/grouped-light ON/OFF: attempt via Kasa
                                               |
                                               v
                                           FarmAction
                                  (success / partial / failed)
```

### `ai_agent.AIRecommendationRun` — `ai_agent_airecommendationrun`

| Field | Django type / rule | Role |
|---|---|---|
| `farm` | FK → Farm, `CASCADE`, related name `ai_recommendation_runs` | Scope |
| `trigger` | `CharField(12)`: `manual`, `scheduled`, `legacy`; default `manual` | Request origin |
| `status` | `CharField(12)`: `pending`, `running`, `completed`, `failed`, `skipped`; default `pending` | Run lifecycle |
| `scheduled_for` | nullable/blank `DateTimeField` | Scheduled slot (when applicable) |
| `input_mode` | `CharField(10)`: `llm`, `vlm`; default `llm` | Effective input mode |
| `provider_name` | `CharField(32, default="unknown")` | Executed provider |
| `model_name` | `CharField(255, default="unknown")` | Executed model |
| `source_images` | M2M → CameraImage (`blank=True`) | Actual chosen visual evidence |
| `source_readings` | M2M → SensorReading (`blank=True`) | Actual sensor evidence |
| `visual_evidence` | `JSONField(default=list)` | Image provenance/selection records |
| `image_observations` | `JSONField(default=list)` | VLM observations |
| `fallback_used` | `BooleanField(default=False)` | Whether run used VLM→LLM fallback |
| `fallback_reason` | `TextField(blank=True, default="")` | Fallback explanation |
| `error` | `TextField(blank=True, default="")` | Failure detail |
| `skip_reason` | `TextField(blank=True, default="")` | Scheduler skip detail |
| `input_freshness_summary` | `JSONField(default=dict)` | Evidence freshness |
| `raw_output` | `TextField(blank=True, default="")` | Model output for audit |
| `created_at` | `DateTimeField(auto_now_add=True)` | Creation |
| `started_at`, `completed_at` | nullable/blank `DateTimeField` | Processing times |

Default ordering: `-created_at`, `-id`. Conditional unique constraint: `unique_ai_schedule_slot` on (`farm`, `scheduled_for`) **only when `trigger='scheduled'`**. Source evidence M2M tables are generated by Django; see `ai_agent/migrations/0005_input_provenance_and_freshness.py`.

### `ai_agent.AIDecision` — `ai_agent_aidecision`

| Field | Django type / rule | Role |
|---|---|---|
| `run` | FK → AIRecommendationRun, `CASCADE`, related name `recommendations` | Parent run |
| `device` | FK → FarmDevice, `CASCADE` | Associated controller |
| `decision_type` | `CharField(50)` | Recommendation action kind |
| `execution_type` | `CharField(20)`, choices `notification`, `automated`; default `notification` | Server-approved execution classification |
| `target_device` | `CharField(20)`, choices `fans`, `light`, `irrigation_pump`, `nutrient_doser`, `ph_doser`, `none`; default `none` | Target category |
| `device_state` | `CharField(20)`, choices `on`, `off`, `none`; default `none` | Suggested state |
| `category` | `CharField(20)`, choices `climate`, `lighting`, `dosing`, `water`, `harvest`, `alert`; default `alert` | Recommendation domain |
| `recommendation` | `TextField` | Human-readable recommendation |
| `explanation` | `TextField` | Reason |
| `confidence_score` | nullable/blank `DecimalField(3,2)` | Model confidence |
| `output_used_fallback` | `BooleanField(default=False)` | Whether output parsing needed fallback; **not the same field as run-level VLM→LLM `fallback_used`** |
| `created_at` | `DateTimeField(auto_now_add=True)` | Creation |

Decisions remain persisted independently from physical actions. The deterministic safety policy revalidates permitted targets and execution types, rather than trusting an LLM/VLM statement to authorize device operations.

### `ai_agent.SafetyCheck` — `ai_agent_safetycheck`

| Field | Django type / rule | Role |
|---|---|---|
| `decision` | O2O → AIDecision, `CASCADE` | One safety result at most per decision |
| `checked_at` | `DateTimeField(auto_now_add=True)` | Check time |
| `result` | `CharField(20)`, choices `passed`, `failed` | Deterministic status |
| `explanation` | nullable/blank `TextField` | Failed/passed rationale |

Safety is checked before automatic actuation. The code uses a confidence threshold of 0.70 and considers relevant sensor freshness/quality and direction/policy checks; see `ai_agent/safety.py`. A model-generated recommendation is **not** permission to actuate a physical device.

### `ai_agent.FarmAction` — `ai_agent_farmaction`

| Field | Django type / rule | Role |
|---|---|---|
| `decision` | FK → AIDecision, `CASCADE`, related name `actions` | Source decision |
| `target_device` | `CharField(20, blank=True, default="")` | Target (fan/light) |
| `powerboard_device_ids` | `JSONField(default=list)` | Logical Kasa device IDs involved |
| `requested_state`, `previous_state`, `confirmed_state` | `CharField(10, blank=True, default="")` each | Requested/before/confirmed state |
| `attempted_at`, `executed_at` | nullable/blank `DateTimeField` | Command lifecycle |
| `result` | nullable/blank `CharField(20)`, choices `success`, `failed`, `partial` | Actual outcome |
| `explanation` | nullable/blank `TextField` | Outcome narrative |
| `hardware_response` | `JSONField(default=dict)` | Hardware bridge response |

Only safety-approved **fan** or **grouped Light Level 1 + Level 2** requests can be executed automatically in the final design. Irrigation, dosing, water and harvest recommendations remain advisory. A partial or failed hardware confirmation must be retained as such. The UI does not have a separate Accept/Decline decision-approval workflow; removal was deliberate.

## 7. Retained supporting/reference models

These ORM models remain present in `backend/telemetry/models.py` and migrations and must **not** be described as dropped tables. They are not the active local-HTTP seven-sensor ingestion schema, however, and their presence does not imply working automated dosing/irrigation.

| Model / table | Actual fields beyond implicit `id` | Relationship / current interpretation |
|---|---|---|
| `NutrientTank` / `telemetry_nutrienttank` | `device` (O2O), `capacity_l` Decimal(6,1), nullable `current_level_l` Decimal(6,1), nullable `last_refill_date`, `updated_at` | One optional reference reservoir per FarmDevice; `CASCADE` |
| `Doser` / `telemetry_doser` | `device` (FK), `chemical_type` Char(50), nullable `concentration` Decimal(10,3), nullable `flow_rate_ml_per_min` Decimal(6,1), `updated_at` | Retained dosing metadata, 1:N from device; `CASCADE` |
| `SafeRange` / `telemetry_saferange` | `sensor_type` Char(50), nullable `min_value`/`max_value` Decimal(10,3), `severity` Char(20) choices `warning`/`critical` | Reference entity; the active AI safety logic uses `ai_agent` config/rules and should not be assumed to read this model for every check |
| `ActuatorStateObservation` / `telemetry_actuatorstateobservation` | `device` FK; `actuator_slug` Slug(80); `state` Char(10) choices `on`/`off`; `measured_at`, `received_at`; `source`, `source_channel_id`, nullable `source_entry_id`; `quality_status`, `quality_notes` | Historical/general externally observed actuator state, distinct from command execution (`FarmAction`); no active ThingSpeak field7 collector |
| `SetpointObservation` / `telemetry_setpointobservation` | `device` FK; `setpoint_slug` Slug(80); `value` Decimal(12,4); `unit` Char(50); `measured_at`, `received_at`; `source`, `source_channel_id`, nullable `source_entry_id`; `quality_status`, `quality_notes` | Historical/general externally observed target, not the AI control policy; no active ThingSpeak field8 collector |

Both observation models have `device` FK with `PROTECT`, indexed `measured_at`, `received_at=auto_now_add`, `source` default `manual`, `source_channel_id` default empty string, quality default `unverified`, and their own optional external-entry uniqueness constraints/indexes:

- `ActuatorStateObservation`: composite index `actuator_obs_time_idx` on (`device`, `actuator_slug`, `measured_at`); unique `uniq_external_actuator_obs` on (`device`, `actuator_slug`, `source`, `source_channel_id`, `source_entry_id`).
- `SetpointObservation`: composite index `setpoint_obs_time_idx` on (`device`, `setpoint_slug`, `measured_at`); unique `uniq_external_setpoint_obs` on (`device`, `setpoint_slug`, `source`, `source_channel_id`, `source_entry_id`).

Their retained source-entry fields support schema compatibility/general observation history. They **do not** evidence an operational external-entry backfill/deduplication service in the final runtime.

## 8. Key constraints, deletion and migration compatibility

### Relationship and invariant register

| Model | Database constraint or ORM relationship | Consequence |
|---|---|---|
| FarmDevice | global unique `slug`; FK Farm `CASCADE` | Machine identity is unique across farms |
| FarmLevel | `CHECK level_number IN (1,2)` and unique (`device`, `level_number`) | No duplicate Top/Bottom for a controller |
| Sensor | unique (`device`, `slug`) | Normalized sensor identity within controller |
| SensorReading | FK Sensor `PROTECT`; indexes/conditional external ID fields described above | Prevents accidental deletion of sensor row while readings still reference it, subject to explicit controlled deletion procedure |
| CameraImage | FK Camera `PROTECT` | Camera with retained images cannot simply be hard-deleted; operator flow archives cameras |
| SensorIngestConfiguration | O2O device `CASCADE` | One active config row per controller |
| PowerboardConfiguration | O2O farm `CASCADE` | One physical-board address pair per farm |
| AIConfiguration | O2O farm `CASCADE` | One provider/schedule config per farm |
| AIRecommendationRun | conditional unique scheduled (`farm`, `scheduled_for`) | Scheduled slot idempotence for non-NULL slots; does not restrict manual runs |
| SafetyCheck | O2O decision `CASCADE` | At most one check row per decision |
| FarmAction | FK decision `CASCADE` | Multiple recorded actuation attempts may relate to one decision |
| BatchPlacement | FK batch/area `CASCADE` and implicit `id` PK | Placement history, no composite PK or special DB active-placement uniqueness |

**Deletion:** `telemetry.farm_deletion.purge_farm()` is the custom cleanup path for deleting an entire farm and its owned media/history. Do not assume a naive ORM `.delete()` is sufficient for related `PROTECT` evidence rows and filesystem JPEGs. Camera archive is the supported operator action instead of hard-delete. A database backup must be accompanied by matching `backend/media` contents and required private keys/configuration.

### Historical migrations: do not rewrite or remove them

- `sensor_ingest/0001_initial.py` is historical; `sensor_ingest/0002_remove_legacy_ingestion_audit.py` deletes `IngestionSourceState` and `IngestionRecord`; `0003_sensoringestconfiguration.py` introduces active configuration.
- `cv` historical migrations remain in the migration graph. `cv/models.py` currently declares no active model; migrations `0004` and `0006` remove former CV measurement/analysis models. **Do not resurrect LeafyCV or delete migration history.**
- `telemetry/0012`–`0014` align RTSP/camera quality metadata and remove obsolete ROI/CV camera fields; `ai_agent/0004`–`0005` track current runs/actions and input provenance; `powerboard_control/0001_initial.py` creates farm-scoped Kasa config.
- Add new schema changes via fresh Django migrations and review backwards compatibility; never edit previously applied migrations to make this documentation agree.

## 9. Configuration ownership and operational flows

| Concern | Bootstrap / initial value | **Normal runtime authority** | Operator / maintainer action |
|---|---|---|---|
| Farm/controller + default sensor definitions | `bootstrap_leafy`, `seed_sensors`, `provision_farm` | `Farm`, `FarmDevice`, `FarmLevel`, `Sensor` rows | Farm creation / seed management |
| Sensor endpoint/timing | `.env` seeds designated Lab device only | `SensorIngestConfiguration` DB row | Settings → Sensor ingestion / farm API |
| Physical board IPs | `.env` seeds initial Lab farm only | `PowerboardConfiguration` DB row | Settings → Powerboard / farm API |
| AI provider/model/window | defaults and initial row creation | `AIConfiguration` DB row | Settings → AI configuration |
| Camera settings | `LEAFY_CAMERA_1_*` for named bootstrap camera | `Camera` DB row; named Lab camera may be refreshed from env during bootstrap | Settings → Cameras; inspect bootstrap when editing Lab camera |
| Sensor history | HTTP JSON responses | `SensorReading` rows | Farm Overview / History / AI evidence |
| Image evidence | RTSP camera frames | `CameraImage` row plus media JPEG | History → Cameras / AI Agent |
| AI outcomes | AI provider output and local rules | AIRecommendationRun → AIDecision → SafetyCheck → FarmAction | AI Agent / History |
| Outlet mapping | `powerboard_control/config.py` constants | Same immutable logical mapping unless code is deliberately revised | Do **not** edit via IP Settings |

The normal sensor path is `sensor_ingest.services.collector.SensorCollector` → mapper → `SensorReading`. It currently uses the collection time for `measured_at`; it does not import original ThingSpeak timestamps. The background workers are within the Django development process (`leafy_runtime`) and are not separate Docker Compose services. For multi-worker deployment, move the scheduler to a dedicated job service with coordination; do not assume the in-process development scheduler is horizontally scalable.

### Configuration and storage safety

- `.env` is local/private deployment configuration and must remain gitignored. `.env.example` is the onboarding template, **not** a place to store live secrets.
- AI API keys stored in `AIConfiguration` are encrypted by the application; retain `AI_SETTINGS_ENCRYPTION_KEY` securely for future decryption and backup restore.
- User registration/JWT authentication is implemented by Django's auth + `accounts` app; no custom user model is declared in this schema reference.
- This deployment uses SQLite and local media on development/lab hardware. It is **not** described as a production-hardened multi-tenant control system.

## 10. Verification, change procedure and limitations

### Maintainer verification (read-only unless testing requires otherwise)

Run in the current backend container from the repository root, after starting Docker and configuring the local `.env`:

```powershell
docker compose exec backend python manage.py check
docker compose exec backend python manage.py showmigrations
docker compose exec backend python manage.py makemigrations --check --dry-run
# On a disposable/test database, verify migrations and run relevant tests:
docker compose exec backend python manage.py test telemetry sensor_ingest ai_agent powerboard_control
```

For actual record counts, use the Django shell on the **intended test database** and inspect `Farm`, `Sensor`, `SensorReading`, `CameraImage`, `AIRecommendationRun`, and `PowerboardConfiguration` without changing existing data. Hardware-linked runtime functionality requires Lab network access; DB migration checks alone do not prove sensors, RTSP or Kasa wiring.

When changing an entity or endpoint, update (1) its Django model/serializer/service, (2) migrations if persisted fields change, (3) associated tests, (4) this schema reference, (5) relevant subsystem README/API notes and (6) the System Maintenance Document if its design/maintenance contract changes. Back up **database + media + private deployment secrets** before migrations and verify restore on a separate copy.

### Known limits and intentional omissions

- Seven **normalized measurements** are represented by seven Sensor definitions, not seven independent HTTP endpoints.
- The historical external-entry metadata columns in SensorReading and supporting observation models are real schema fields but are *not* evidence of current ThingSpeak operation.
- Image technical quality gates do not diagnose basil diseases or produce reliable plant count, pixel-to-centimetre growth or harvest predictions.
- Manual Kasa powerboard state/control is distinct from AI automated actuation. Only fan/grouped lights are eligible for the latter, after deterministic safety checks.
- `growth`/`farm_state` do not introduce their own current ORM model tables; `cv` migrations persist for compatibility only.
- Current validation evidence and the SMD describe a **development/lab handover**, not an independently security-certified production deployment.

**Primary related documentation:** root `README.md`; `backend/sensor_ingest/README.md`; `backend/camera_capture/README.md`; `backend/powerboard_control/README.md`; final `System Maintenance Document.docx` (Chapters 5–11, 13–15). This file is the source-code-aligned detail supplement to the SMD, not a replacement for Django migrations.
