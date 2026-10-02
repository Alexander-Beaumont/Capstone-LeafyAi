# Leafy AI — Database Schema v2

> Revised to match the physical vertical farming device workflow and the project proposal requirements.

---

## Table of Contents

1. [Core Farm Structure](#1-core-farm-structure)
2. [Growing Areas](#2-growing-areas)
3. [Batch Management](#3-batch-management)
4. [Camera & Vision](#4-camera--vision)
5. [Sensors](#5-sensors)
6. [Device-level Hardware](#6-device-level-hardware)
7. [Sensor Ingestion & External Observations](#7-sensor-ingestion--external-observations)
8. [Safety Layer](#8-safety-layer)
9. [AI Decision Chain](#9-ai-decision-chain)

---

## 1. Core Farm Structure

### FARM

| Column | Type | Constraints | Description |
|---|---|---|---|
| `farm_id` | INTEGER AUTO-INCREMENT | PK | Unique identifier |
| `name` | VARCHAR(255) | NOT NULL | Farm name |
| `location` | VARCHAR(255) | | Physical location |

### FARMDEVICE

A vertical farming device is the physical hardware unit. Each device has 2 levels, a shared nutrient tank, a shared water pump, and a shared doser.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `device_id` | INTEGER AUTO-INCREMENT | PK | Unique identifier |
| `farm_id` | INTEGER AUTO-INCREMENT | FK → FARM, NOT NULL | Owning farm |
| `name` | VARCHAR(255) | NOT NULL | Human-readable name |
| `slug` | VARCHAR(80) | UNIQUE, NOT NULL | Stable machine identifier used by integrations |
| `device_type` | VARCHAR(100) | | Model / variant |

**Relationships:** FARM — DEVICE: 1:M

### FARMLEVEL

Each device has exactly 2 levels. The top level (level 1) contains the seedling chamber and the early-growth area. The bottom level (level 2) is the main growth area for mature plants.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `farm_level_id` | INTEGER AUTO-INCREMENT | PK | Unique identifier |
| `device_id` | INTEGER AUTO-INCREMENT | FK → DEVICE, NOT NULL | Parent device |
| `level_number` | INTEGER | NOT NULL, CHECK (1 or 2) | 1 = top, 2 = bottom |

**Relationships:** DEVICE — FARMLEVEL: 1:M

---

## 2. Growing Areas

### GROWING_AREA

Each level is divided into distinct growing areas with different purposes.

- **Top level (level 1):** 2 areas — Seedling Chamber (enclosed, ¼ of the level) and Early Growth Area (open, ¾ of the level, weeks 1–3).
- **Bottom level (level 2):** 1 area — Main Growth Area (mature plants).

| Column | Type | Constraints | Description |
|---|---|---|---|
| `growing_area_id` | INTEGER AUTO-INCREMENT | PK | Unique identifier |
| `farm_level_id` | INTEGER AUTO-INCREMENT | FK → FARMLEVEL, NOT NULL | Parent level |
| `name` | VARCHAR(255) | NOT NULL | e.g. "Seedling Chamber" |
| `slot_count` | INTEGER | NOT NULL | Number of NFT positions |

**Relationships:** FARMLEVEL — GROWING_AREA: 1:M

---

## 3. Batch Management

### PLANTBATCH

A group of plants of the same type planted together on the same date. The batch moves through growing stages as a cohort.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `batch_id` | INTEGER AUTO-INCREMENT | PK | Unique identifier |
| `plant_type` | VARCHAR(100) | NOT NULL | e.g. "Sweet Basil" |
| `planting_date` | DATE | NOT NULL | Date seeded/planted |
| `growth_stage` | VARCHAR(50) | NOT NULL, CHECK IN ('seedling', 'early_growth', 'mature') | Current stage |
| `status` | VARCHAR(50) | NOT NULL, CHECK IN ('active', 'harvested', 'failed') | Lifecycle status |

### BATCH_PLACEMENT

Tracks where a batch is located over time. This is the key table for the movement workflow: a batch starts in the seedling chamber, then moves to the early growth area, then to the main growth area.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `batch_id` | INTEGER AUTO-INCREMENT | COMPOSITE PK, FK → PLANTBATCH, NOT NULL | The batch |
| `growing_area_id` | INTEGER AUTO-INCREMENT | COMPOSITE PK, FK → GROWINGAREA, NOT NULL | The growing area occupied |
| `start_date` | TIMESTAMP | NOT NULL | When the batch was placed here |
| `end_date` | TIMESTAMP | NULLABLE | When the batch was moved out (null = current) |

**Relationships:**
- PLANTBATCH — BATCH_PLACEMENT: 1:M
- GROWINGAREA — BATCH_PLACEMENT: 1:M

---

## 4. Camera Images and VLM Quality

### CAMERA

Multiple cameras per level for visual monitoring.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `camera_id` | INTEGER AUTO-INCREMENT | PK | Unique identifier |
| `farm_level_id` | INTEGER AUTO-INCREMENT | FK → FARMLEVEL, NOT NULL | Which level the camera monitors |
| `name` | VARCHAR(255) | NOT NULL | e.g. "Top Level - Left" |
| `position` | VARCHAR(100) | | Physical position description |
| `source_type` | VARCHAR(20) | NOT NULL, CHECK IN (RTSP) | Camera input type |
| `ip_address` | VARCHAR(255) | | IP address for RTSP |
| `rtsp_port` | INTEGER | | RTSP port, normally 554 |
| `rtsp_path` | VARCHAR(255) | | RTSP stream path |
| `enabled` | BOOLEAN | NOT NULL, DEFAULT TRUE | Whether camera is active |
| `is_archived` | BOOLEAN | NOT NULL, DEFAULT FALSE | Soft-delete state |
| `capture_interval_minutes` | INTEGER | NOT NULL, DEFAULT 30 | Capture interval |
| `active_start_time` | TIME | | Start of capture window |
| `active_end_time` | TIME | | End of capture window |

**Relationships:** FARMLEVEL — CAMERA: 1:M

### CAMERAIMAGE

Captured frames from cameras.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `image_id` | INTEGER AUTO-INCREMENT | PK | Unique identifier |
| `camera_id` | INTEGER AUTO-INCREMENT | FK → CAMERA, NOT NULL | Source camera |
| `captured_at` | TIMESTAMP | NOT NULL | When captured |
| `path` | VARCHAR(500) | NOT NULL | Storage path |
| `vlm_ready` | BOOLEAN | DEFAULT FALSE | Whether the technical gate permits VLM input |
| `quality_status` | VARCHAR(16) | DEFAULT UNKNOWN | PASS, WARN, or FAIL |
| `quality_flags` | JSON | DEFAULT [] | Deterministic technical diagnostics |
| `quality_message` | TEXT | DEFAULT '' | Human-readable quality result |
| `quality_metrics` | JSON | DEFAULT {} | Exposure, focus, resolution, and colour diagnostics |

**Relationships:** CAMERA — CAMERAIMAGE: 1:M

---

## 5. Sensors

### SENSOR

Sensors monitor physical environmental conditions. A sensor is device-specific, so it reflects the conditions of the whole hydroponic device unless another scope is introduced later. External integrations address sensors by stable slugs rather than auto-increment database IDs.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `sensor_id` | INTEGER AUTO-INCREMENT | PK | Unique database identifier |
| `device_id` | INTEGER AUTO-INCREMENT | FK → DEVICE, NOT NULL | Device this sensor belongs to |
| `slug` | VARCHAR(80) | NOT NULL, UNIQUE PER DEVICE | Stable integration identifier, e.g. `water_ph` |
| `sensor_type` | VARCHAR(50) | NOT NULL | Canonical safety/farm-state type, e.g. `ph`, `ec`, `humidity` |
| `unit` | VARCHAR(50) | NOT NULL | e.g. `°C`, `%`, `pH`, `µS/cm`, `cm` |
| `enabled` | BOOLEAN | NOT NULL, DEFAULT TRUE | Whether ingestion should create new readings |
| `expected_interval_seconds` | INTEGER | NULLABLE | Expected source update interval |
| `stale_after_seconds` | INTEGER | NULLABLE | Sensor-specific farm-state freshness threshold |

**Relationships:**
- DEVICE — SENSOR: 1:M

### SENSORREADING

Append-oriented time-series measurements from physical sensors. `measured_at` comes from the source system; `received_at` records when Leafy AI persisted it.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `reading_id` | INTEGER AUTO-INCREMENT | PK | Unique identifier |
| `sensor_id` | INTEGER AUTO-INCREMENT | FK → SENSOR, NOT NULL, PROTECT | Source sensor |
| `value` | DECIMAL(12,4) | NOT NULL | Measured value |
| `measured_at` | TIMESTAMP | NOT NULL, INDEXED | When the source says the physical measurement occurred |
| `received_at` | TIMESTAMP | NOT NULL, AUTO | When Leafy AI stored the observation |
| `source` | VARCHAR(50) | NOT NULL | e.g. `thingspeak`, `manual` |
| `source_channel_id` | VARCHAR(100) | | External channel/source identifier |
| `source_entry_id` | BIGINT | NULLABLE | ThingSpeak `entry_id` or equivalent source identity |
| `quality_status` | VARCHAR(20) | CHECK IN (`valid`, `unverified`, `suspect`) | Observation-quality classification, independent of crop safety |
| `quality_notes` | VARCHAR(255) | | Quality explanation |

External readings are unique by `(sensor, source, source_channel_id, source_entry_id)`.

**Relationships:** SENSOR — SENSORREADING: 1:M

---

## 6. Device-level Hardware

### NUTRIENT_TANK

The nutrient reservoir at the bottom of each device. Monitored for water level (refill alerts) and nutrient concentration.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `tank_id` | INTEGER AUTO-INCREMENT | PK | Unique identifier |
| `device_id` | INTEGER AUTO-INCREMENT | FK → DEVICE, NOT NULL | Parent device |
| `capacity_l` | DECIMAL(6,1) | NOT NULL | Total capacity in litres |
| `current_level_l` | DECIMAL(6,1) | | Current water level |
| `last_refill_date` | TIMESTAMP | | When the tank was last refilled |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | |

**Relationships:** DEVICE — NUTRIENT_TANK: 1:1 (a device can only have 1 tank)

### DOSER

Relay-controlled dosing pumps that add nutrients or pH adjusters to the shared water supply.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `doser_id` | INTEGER AUTO-INCREMENT | PK | Unique identifier |
| `device_id` | INTEGER AUTO-INCREMENT | FK → DEVICE, NOT NULL | Parent device |
| `chemical_type` | VARCHAR(50) | NOT NULL | e.g. 'nutrient_a', 'nutrient_b', 'ph_up', 'ph_down' |
| `concentration` | DECIMAL(10,3) | | Current concentration setting |
| `flow_rate_ml_per_min` | DECIMAL(6,1) | | Calibrated flow rate |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | |

**Relationships:** DEVICE — DOSER: 1:M

### POWERBOARD_CONFIGURATION

Stores the two physical TP-Link/Kasa strip addresses assigned to a farm. Logical outlet IDs remain fixed in application configuration; only the two strip addresses vary by farm. The Lab `.env` values seed the initial farm once, after which this database row is authoritative for farm-scoped runtime operations.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER AUTO-INCREMENT | PK | Unique identifier |
| `farm_id` | INTEGER | FK → FARM, NOT NULL, UNIQUE | One Powerboard configuration per farm |
| `powerboard_1_ip` | IP ADDRESS / VARCHAR | NULLABLE | Physical address of board 1 |
| `powerboard_2_ip` | IP ADDRESS / VARCHAR | NULLABLE | Physical address of board 2 |
| `updated_at` | TIMESTAMP | NOT NULL, AUTO UPDATE | Last configuration update |

**Relationships:** FARM — POWERBOARD_CONFIGURATION: 1:0..1

Current fixed outlet contract:

| Device ID | Logical device | Board | Child index |
|---:|---|---|---:|
| 1 | pH Doser | board 1 | 0 |
| 2 | EC Doser | board 1 | 1 |
| 3 | Irrigation Pump | board 1 | 2 |
| 4 | Farm Fan | board 2 | 0 |
| 5 | Light Level 1 | board 2 | 1 |
| 6 | Light Level 2 | board 2 | 2 |

The Django table created by `powerboard_control/migrations/0001_initial.py` is `powerboard_control_powerboardconfiguration`.

---

## 7. Sensor Ingestion & External Observations

The `sensor_ingest` Django app is the integration boundary between the owner-provided ThingSpeak channel and Leafy AI's internal telemetry database. It retrieves data, validates source identity/timestamps, normalises external fields, deduplicates by source entry ID, performs startup/periodic backfill, and records ingestion health. It does **not** decide whether a value is safe for basil or whether hardware should run.

### ACTUATORSTATEOBSERVATION

ThingSpeak field 7 reports irrigation-pump relay state. This is stored as an observed actuator state rather than pretending the relay is a sensor.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER AUTO-INCREMENT | PK | Unique identifier |
| `device_id` | INTEGER | FK → FARMDEVICE, NOT NULL, PROTECT | Device being observed |
| `actuator_slug` | VARCHAR(80) | NOT NULL | e.g. `irrigation_pump` |
| `state` | VARCHAR(10) | CHECK IN (`on`, `off`) | Observed state |
| `measured_at` | TIMESTAMP | NOT NULL | Source measurement time |
| `received_at` | TIMESTAMP | NOT NULL, AUTO | Leafy AI receipt time |
| `source` | VARCHAR(50) | NOT NULL | External provider |
| `source_channel_id` | VARCHAR(100) | | External channel |
| `source_entry_id` | BIGINT | NULLABLE | External entry ID |
| `quality_status` | VARCHAR(20) | | Observation quality |
| `quality_notes` | VARCHAR(255) | | Quality explanation |

### SETPOINTOBSERVATION

ThingSpeak field 8 reports the owner's target EC. It is stored as an externally observed setpoint, not a physical sensor measurement and not automatically Leafy AI's authoritative control policy.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER AUTO-INCREMENT | PK | Unique identifier |
| `device_id` | INTEGER | FK → FARMDEVICE, NOT NULL, PROTECT | Device whose setpoint was reported |
| `setpoint_slug` | VARCHAR(80) | NOT NULL | `target_ec` |
| `value` | DECIMAL(12,4) | NOT NULL | Setpoint value |
| `unit` | VARCHAR(50) | NOT NULL | `µS/cm` |
| `measured_at` | TIMESTAMP | NOT NULL | Source observation time |
| `received_at` | TIMESTAMP | NOT NULL, AUTO | Leafy AI receipt time |
| `source` | VARCHAR(50) | NOT NULL | External provider |
| `source_channel_id` | VARCHAR(100) | | External channel |
| `source_entry_id` | BIGINT | NULLABLE | External entry ID |
| `quality_status` | VARCHAR(20) | | Observation quality |
| `quality_notes` | VARCHAR(255) | | Quality explanation |

### INGESTIONSOURCESTATE

Operational health for an external feed. Connection health and source-data freshness are tracked independently so HTTP success is not mistaken for fresh telemetry.

Key fields include `last_attempt_at`, `last_http_success_at`, `last_new_entry_at`, `last_source_entry_id`, `last_source_measured_at`, `consecutive_failures`, and the latest error code/message.

### INGESTIONRECORD

One audit row per external source entry. The pair `(source, source_entry_id)` is unique. A SHA-256 hash of the relevant ThingSpeak entry contract prevents an already-ingested entry ID from silently changing. The record also stores whether ingestion was complete/partial/empty plus counts and missing/invalid field lists.

Current ThingSpeak mapping:

| Field | Meaning | Internal representation |
|---|---|---|
| `field1` | Water pH | `SensorReading` / `water_ph` |
| `field2` | Electrical conductivity | `SensorReading` / `electrical_conductivity` |
| `field3` | Water temperature | `SensorReading` / `water_temperature` |
| `field4` | Ambient temperature | `SensorReading` / `ambient_temperature` |
| `field5` | Relative humidity | `SensorReading` / `relative_humidity` |
| `field6` | Reservoir water level | `SensorReading` / `reservoir_water_level` |
| `field7` | Irrigation pump state | `ActuatorStateObservation` |
| `field8` | Target EC | `SetpointObservation` |

---

## 8. Safety Layer

### SAFE_RANGE

Reference ranges used by the safety layer to validate sensor readings and AI-generated setpoints. The proposal states that *"no AI-generated command reaches farm hardware without validation"* and that *"medium/high-risk AI-generated actions must not rely on single readings alone; trend confirmation is required."*

| Column | Type | Constraints | Description |
|---|---|---|---|
| `range_id` | INTEGER AUTO-INCREMENT | PK | Unique identifier |
| `sensor_type` | VARCHAR(50) | NOT NULL | e.g. 'temperature', 'ph', 'ec', 'humidity', 'water_level' |
| `min_value` | DECIMAL(10,3) | | Lower bound (null = no lower bound) |
| `max_value` | DECIMAL(10,3) | | Upper bound (null = no upper bound) |
| `severity` | VARCHAR(20) | NOT NULL, CHECK IN ('warning', 'critical') | 'warning' = alert only, 'critical' = block action |

---

## 9. AI Decision Chain

The active chain is **Recommendation Run → AI Decision → Safety Check → Farm Action or Notification**. Reliable raw images are read directly by the VLM; failed images route the run to the sensor-only LLM.

### AICONFIGURATION / AIRECOMMENDATIONRUN

Each farm has provider/model, encrypted credential, schedule-window, interval, timezone, and image-limit settings. A run records its trigger/status, provider/model, VLM or LLM mode, source images, quality evidence, VLM observations, fallback reason, errors, and timestamps. Scheduled `(farm, scheduled_for)` slots are unique.

### AIDECISION

Every AI recommendation or decision is recorded with a human-readable explanation.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `decision_id` | INTEGER AUTO-INCREMENT | PK | Unique identifier |
| `run_id` | INTEGER AUTO-INCREMENT | FK → AIRECOMMENDATIONRUN, NOT NULL | Parent recommendation run |
| `device_id` | INTEGER AUTO-INCREMENT | FK → DEVICE, NOT NULL | Relevant device (if device-level) |
| `output_used_fallback` | BOOLEAN | NOT NULL | Whether malformed model output required text parsing fallback |
| `decision_type` | VARCHAR(50) | NOT NULL | e.g. 'schedule_update', 'dosing_adjustment', 'lighting_adjustment', 'fan_adjustment', 'harvest_recommendation', 'spacing_adjustment', 'alert' |
| `execution_type` | VARCHAR(20) | NOT NULL, CHECK IN ('notification', 'automated') | Server-derived execution policy |
| `target_device` | VARCHAR(20) | NOT NULL | Fan/light or advisory pump/doser target |
| `device_state` | VARCHAR(20) | NOT NULL, CHECK IN ('on', 'off', 'none') | Requested state for the target hardware |
| `category` | VARCHAR(20) | NOT NULL, CHECK IN ('climate', 'lighting', 'dosing', 'water', 'harvest', 'alert') | Safety category used to select relevant evidence and pass/fail handling |
| `recommendation` | TEXT | NOT NULL | What the AI recommends in plain language |
| `explanation` | TEXT | NOT NULL | Human-readable explanation of why |
| `confidence_score` | DECIMAL(3,2) | | AI confidence (0.00–1.00) |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | |

### SAFETYCHECK

Software-based safety validation result. The proposal states: *"Implement a software-based safety layer so no AI-generated command reaches farm hardware without validation."*

| Column | Type | Constraints | Description |
|---|---|---|---|
| `safety_check_id` | INTEGER AUTO-INCREMENT | PK | Unique identifier |
| `decision_id` | INTEGER AUTO-INCREMENT | FK → AIDECISION, NOT NULL, UNIQUE | The decision being checked (1:1) |
| `checked_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | |
| `result` | VARCHAR(20) | NOT NULL, CHECK IN ('passed', 'failed') | Whether evidence and policy validation passed |
| `explanation` | TEXT | | Why it passed or failed |

**Relationships:** AIDECISION — SAFETYCHECK: 1:1

### FARMACTION

Audited result of a safety-approved automatic fan or grouped-light command. Automatic hardware execution resolves the two physical Powerboard IPs from the recommendation run's farm-specific `POWERBOARD_CONFIGURATION`; an unconfigured farm must fail closed rather than use another farm's addresses.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `action_id` | INTEGER AUTO-INCREMENT | PK | Unique identifier |
| `decision_id` | INTEGER AUTO-INCREMENT | FK → AIDECISION, NOT NULL | Source decision |
| `target_device` | VARCHAR(20) | NOT NULL | Logical fan/light target |
| `powerboard_device_ids` | JSON | NOT NULL | Physical device IDs used |
| `requested_state` | VARCHAR(10) | | Requested on/off state |
| `previous_state` | VARCHAR(10) | | State before execution |
| `confirmed_state` | VARCHAR(10) | | Hardware-confirmed state |
| `attempted_at` | TIMESTAMP | | When execution started |
| `executed_at` | TIMESTAMP | | When executed (null = pending) |
| `result` | VARCHAR(20) | CHECK IN ('success', 'failed', 'partial') | |
| `explanation` | TEXT | | Outcome description |
| `hardware_response` | JSON | DEFAULT {} | Raw normalized powerboard response |

**Relationships:** AIDECISION — FARMACTION: 1:M
