# Leafy AI — Database Schema v2

> Revised to match the physical vertical farming device workflow and the project proposal requirements.

---

## Table of Contents

1. [Core Farm Structure](#1-core-farm-structure)
2. [Growing Areas & Slots](#2-growing-areas--slots)
3. [Batch Management](#3-batch-management)
4. [Camera & Vision](#4-camera--vision)
5. [Sensors](#5-sensors)
6. [Device-level Hardware](#6-device-level-hardware)
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

## 2. Growing Areas & Slots

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

### SLOT

An individual NFT position within a growing area. Each slot can hold one plant (or one cluster in the seedling stage). The telescopic NFT channels allow spacing to be adjusted as plants mature.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `slot_id` | INTEGER AUTO-INCREMENT | PK | Unique identifier |
| `growing_area_id` | INTEGER AUTO-INCREMENT | FK → GROWING_AREA, NOT NULL | Parent area |
| `slot_number` | INTEGER | NOT NULL | Position number within the area |
| `row` | INTEGER | | Row index (for multi-row layouts) |
| `column` | INTEGER | | Column index |

**Unique constraint:** (`growing_area_id`, `slot_number`)

**Relationships:** GROWING_AREA — SLOT: 1:M
**Relationships:** CAMERA — SLOT: M:M

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

Tracks where a batch is located over time. This is the key table for the movement workflow: a batch starts in the seedling chamber, then moves to the early growth area, then to the main growth area. Each placement can span multiple slots.

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

## 4. Camera & Vision

### CAMERA

Multiple cameras per level for visual monitoring.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `camera_id` | INTEGER AUTO-INCREMENT | PK | Unique identifier |
| `farm_level_id` | INTEGER AUTO-INCREMENT | FK → FARMLEVEL, NOT NULL | Which level the camera monitors |
| `name` | VARCHAR(255) | NOT NULL | e.g. "Top Level - Left" |
| `position` | VARCHAR(100) | | Physical position description |
| `source_type` | VARCHAR(20) | NOT NULL, CHECK IN (RTSP, WEBCAM) | Camera input type |
| `ip_address` | VARCHAR(255) | | IP address for RTSP |
| `rtsp_port` | INTEGER | | RTSP port, normally 554 |
| `webcam_index` | INTEGER | | Local webcam index, e.g. 0, 1, 2 |
| `lighting_mode` | VARCHAR(20) | NOT NULL, CHECK IN (NORMAL, MAGENTA) | Lighting/preprocessing mode |
| `roi_points` | JSON | | Monitoring Region of Interest |
| `calibration_start_x` | DECIMAL(8,6) | | Calibration line start X, normalized 0-1 |
| `calibration_start_y` | DECIMAL(8,6) | | Calibration line start Y, normalized 0-1 |
| `calibration_end_x` | DECIMAL(8,6) | | Calibration line end X, normalized 0-1 |
| `calibration_end_y` | DECIMAL(8,6) | | Calibration line end Y, normalized 0-1 |
| `calibration_length_cm` | DECIMAL(8,2) | | Real-world calibration length |
| `enabled` | BOOLEAN | NOT NULL, DEFAULT TRUE | Whether camera is active |

**Relationships:** FARMLEVEL — CAMERA: 1:M
**Relationships:** SLOT — CAMERA: M:M

### CAMERA_SLOT_POSITION

| Column | Type | Constraints | Description |
|---|---|---|---|
| `camera_id` | INTEGER AUTO-INCREMENT | COMPOSITE PK, FK → CAMERA, NOT NULL | Camera |
| `slot_id` | TIMESTAMP | COMPOSITE PK, FK → SLOT, NOT NULL | Physical slot |
| `centre_x` | DECIMAL(8,6) | NOT NULL | Slot centre X |
| `centre_y` | DECIMAL(8,6) | NOT NULL | Slot centre Y |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Creation time |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last adjustment |

### CAMERAIMAGE

Captured frames from cameras.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `image_id` | INTEGER AUTO-INCREMENT | PK | Unique identifier |
| `camera_id` | INTEGER AUTO-INCREMENT | FK → CAMERA, NOT NULL | Source camera |
| `timestamp` | TIMESTAMP | NOT NULL | When captured |
| `path` | VARCHAR(500) | NOT NULL | Storage path |

**Relationships:** CAMERA — CAMERAIMAGE: 1:M

### IMAGEANALYSIS

Results from running vision models on captured images.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `analysis_id` | INTEGER AUTO-INCREMENT | PK | Unique identifier |
| `image_id` | INTEGER AUTO-INCREMENT | FK → CAMERAIMAGE, NOT NULL | Source image |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | |
| `total_canopy_coverage` | DECIMAL(5,2) | | Percentage of image covered by foliage |
| `visible_plant_count` | INTEGER | | Number of plants detected |
| `measurement_valid` | BOOLEAN | DEFAULT TRUE | Whether the analysis is reliable |
| `processing_time_ms` | INTEGER | | Time taken to process |

**Relationships:** CAMERAIMAGE — IMAGEANALYSIS: 1:M

### PLANTVISIONMEASUREMENT

Per-plant measurements extracted from image analysis. Each measurement is linked to a specific slot (identifying the plant) and optionally to a batch.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `measurement_id` | INTEGER AUTO-INCREMENT | PK | Unique identifier |
| `analysis_id` | INTEGER AUTO-INCREMENT | FK → IMAGEANALYSIS, NOT NULL | Parent analysis |
| `slot_id` | INTEGER AUTO-INCREMENT | FK → SLOT | Which slot this plant is in |
| `canopy_coverage` | DECIMAL(5,2) | | Coverage for this specific plant |
| `width_px` | INTEGER | | Width in pixels |
| `height_px` | INTEGER | | Height in pixels |
| `width_cm` | DECIMAL(5,1) | | Estimated width in cm |
| `height_cm` | DECIMAL(5,1) | | Estimated height in cm |
| `green_percentage` | DECIMAL(5,2) | | Healthy green foliage estimate |
| `yellow_percentage` | DECIMAL(5,2) | | Yellow/discoloured foliage estimate |
| `crowding_percentage` | DECIMAL(5,2) | | Overlap/crowding estimate |
| `growth_stage` | VARCHAR(50) | | Detected stage of this plant |
| `growth_change` | DECIMAL(8,2) | | Change from previous valid scheduled measurement |
| `visible` | BOOLEAN | DEFAULT TRUE | Whether the plant is clearly visible |
| `measurement_valid` | BOOLEAN | DEFAULT TRUE | |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | |

**Relationships:**
- IMAGEANALYSIS — PLANTVISIONMEASUREMENT: 1:M
- SLOT — PLANTVISIONMEASUREMENT: 1:M

---

## 5. Sensors

### SENSOR

Sensors monitor environmental conditions. A sensor is device-specific, which means it reflects the conditions of the whole device.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `sensor_id` | INTEGER AUTO-INCREMENT | PK | Unique identifier |
| `device_id` | INTEGER AUTO-INCREMENT | FK → DEVICE, NOT NULL | Device this sensor belongs to |
| `sensor_type` | VARCHAR(50) | NOT NULL | e.g. 'temperature', 'humidity', 'ph', 'ec', 'water_level', 'flow' |
| `unit` | VARCHAR(50) | NOT NULL | e.g. '°C', '%', 'pH', 'µS/cm', 'L', 'L/min' |

**Relationships:**
- DEVICE — SENSOR: 1:M 

### SENSORREADING

Time-series data from sensors.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `reading_id` | INTEGER AUTO-INCREMENT | PK | Unique identifier |
| `sensor_id` | INTEGER AUTO-INCREMENT | FK → SENSOR, NOT NULL | Source sensor |
| `timestamp` | TIMESTAMP | NOT NULL | When the reading was taken |
| `value` | DECIMAL(10,3) | NOT NULL | Measured value |

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

The decision chain follows: **AI Decision → Safety Check → Human Approval → Farm Action**.

Each step is recorded in a separate table for auditability.

### AIDECISION

Every AI recommendation or decision is recorded with a human-readable explanation.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `decision_id` | INTEGER AUTO-INCREMENT | PK | Unique identifier |
| `device_id` | INTEGER AUTO-INCREMENT | FK → DEVICE, NOT NULL | Relevant device (if device-level) |
| `decision_type` | VARCHAR(50) | NOT NULL | e.g. 'schedule_update', 'dosing_adjustment', 'lighting_adjustment', 'fan_adjustment', 'harvest_recommendation', 'spacing_adjustment', 'alert' |
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
| `result` | VARCHAR(20) | NOT NULL, CHECK IN ('passed', 'failed', 'requires_review') | |
| `explanation` | TEXT | | Why it passed or failed |

**Relationships:** AIDECISION — SAFETYCHECK: 1:1

### HUMANAPPROVAL

Human review of AI decisions. The proposal states: *"Require human approval for irrigation and dosing actions initially, with a path to automatic control for low-risk actions such as lights and fans."*

| Column | Type | Constraints | Description |
|---|---|---|---|
| `approval_id` | INTEGER AUTO-INCREMENT | PK | Unique identifier |
| `decision_id` | INTEGER AUTO-INCREMENT | FK → AIDECISION, NOT NULL, UNIQUE | The decision being reviewed (1:1) |
| `reviewed_at` | TIMESTAMP | | When reviewed (null = pending) |
| `result` | VARCHAR(20) | CHECK IN ('approved', 'denied', 'overridden') | |
| `comment` | TEXT | | Reviewer's notes |

**Relationships:** AIDECISION — HUMANAPPROVAL: 1:1

### FARMACTION

Record of an executed farm action. A single decision may result in multiple actions (e.g., adjust lights and fan together).

| Column | Type | Constraints | Description |
|---|---|---|---|
| `action_id` | INTEGER AUTO-INCREMENT | PK | Unique identifier |
| `decision_id` | INTEGER AUTO-INCREMENT | FK → AIDECISION, NOT NULL | Source decision |
| `executed_at` | TIMESTAMP | | When executed (null = pending) |
| `result` | VARCHAR(20) | CHECK IN ('success', 'failed', 'partial') | |
| `explanation` | TEXT | | Outcome description |

**Relationships:** AIDECISION — FARMACTION: 1:M
