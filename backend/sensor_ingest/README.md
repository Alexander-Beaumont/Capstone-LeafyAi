# LeafyAI Sensor Ingestion

`backend/sensor_ingest` owns the current physical sensor-ingestion boundary for LeafyAI.

It reads the configured local HTTP devices, validates/normalizes their payloads, persists valid observations as `telemetry.SensorReading`, and records runtime health on `SensorIngestConfiguration`.

## Runtime flow

```text
SensorIngestConfiguration
        |
        +--> water-quality HTTP endpoint
        |
        +--> ambient/water-level HTTP endpoint
        |
        v
SensorCollector
        |
        v
normalize_payloads()
        |
        v
SensorReading
        |
        v
farm_state
        |
        v
dashboard / history / AI Agent
```

The backend background worker calls `collect_due_configurations()` when `LEAFY_RUNTIME_ENABLED=true`.

## Standard sensor definitions

The standard controller owns seven sensor definitions:

| Slug | Type | Unit | Source | Payload key | Validity key |
| --- | --- | --- | --- | --- | --- |
| `water_ph` | `ph` | pH | water quality | `ph` | `ph_valid` |
| `electrical_conductivity` | `ec` | uS/cm | water quality | `ec` | `ec_valid` |
| `water_temperature` | `water_temperature` | °C | water quality | `water_temperature_c` | `water_temperature_valid` |
| `ambient_temperature` | `ambient_temperature` | °C | ambient | `ambient_temperature_c` | `ambient_valid` |
| `relative_humidity` | `humidity` | % | ambient | `humidity_percent` | `ambient_valid` |
| `dew_point` | `dew_point` | °C | ambient | `dew_point_c` | `ambient_valid` |
| `reservoir_water_level` | `water_level` | cm | ambient | `water_level` | `water_level_valid` |

The stable slugs above are shared by sensor ingestion, farm-state generation and the AI/safety layer.

## Current Lab endpoints

Defaults in `.env.example` are:

```env
LEAFY_WATER_QUALITY_URL=http://192.168.1.100/readings
LEAFY_AMBIENT_SENSOR_URL=http://192.168.1.111:8080/readings
```

For a normal farm created from the UI, the sensor-ingest URLs can be edited through the farm-scoped ingestion configuration API.

## Farm provisioning

`telemetry.farm_provisioning.provision_farm()` is called when a new `Farm` is created.

It creates:

```text
Farm
└── Controller FarmDevice
    ├── seven standard Sensor rows
    ├── Farm Level 1
    └── Farm Level 2
```

`ensure_sensor_definitions()` is the canonical helper used to create/update the standard sensor rows.

## Collection semantics

`SensorCollector.collect()` treats both physical HTTP endpoints as one collection cycle.

```text
validate configuration
    -> GET water-quality payload
    -> GET ambient payload
    -> normalize measurements
    -> optionally persist SensorReading rows
```

If either HTTP request fails, returns invalid JSON, or does not return a JSON object, the collection raises an error before the cycle is persisted.

When both endpoints respond successfully, the mapper evaluates each measurement individually:

- a hardware validity flag must be `true`
- the payload field must be present
- the value must be numeric and storable
- basic physical-domain checks may mark a value `suspect`

Measurements that are missing or explicitly invalid are omitted from that cycle and reported in `missing_sensors` / `invalid_sensors`. Other valid normalized measurements can still be stored.

Crop operating ranges are not enforced by ingestion. They belong to the AI safety/control layer.

Persisted physical readings use:

```text
source = local_http
source_channel_id = water_quality | ambient
```

## Runtime-editable configuration

`SensorIngestConfiguration` stores, per controller:

```text
enabled
water_quality_url
ambient_sensor_url
poll_interval_seconds
sensor_stale_threshold_seconds
last_attempt_at
last_success_at
last_error
consecutive_failures
```

The environment values are used to bootstrap the initial Lab configuration. The database configuration is then editable through the operator API.

Updating poll/stale timing propagates the timing values to the controller's `Sensor` rows.

## Operator API

Current routes:

```text
GET   /api/farms/{farm_id}/sensor-ingest/
GET   /api/farms/{farm_id}/sensor-ingest/{device_id}/
PATCH /api/farms/{farm_id}/sensor-ingest/{device_id}/

POST  /api/farms/{farm_id}/sensor-ingest/{device_id}/test/
POST  /api/farms/{farm_id}/sensor-ingest/{device_id}/collect/
```

`test/` performs the real fetch and validation path with `store=False`.

`collect/` performs the same path and persists the resulting readings.

The per-device operation lock prevents manual test/collect requests and the background worker from collecting the same controller concurrently.

## Scheduling and failure backoff

The background runtime checks enabled configurations frequently, while each configuration's `poll_interval_seconds` decides whether it is due.

After failures, the runtime applies bounded exponential backoff using:

```env
SENSOR_INGEST_FAILURE_BACKOFF_BASE_SECONDS=5
SENSOR_INGEST_FAILURE_BACKOFF_MAX_SECONDS=300
```

A failure on one controller does not stop other configured controllers from being processed.

## Important files

```text
sensor_ingest/
├── management/
│   └── commands/
│       ├── collect_sensors.py
│       └── seed_sensors.py
├── migrations/
├── services/
│   ├── collector.py
│   ├── configuration.py
│   ├── mapper.py
│   └── runtime.py
├── tests/
│   ├── test_collector.py
│   ├── test_mapper.py
│   └── test_seed_command.py
├── exceptions.py
├── models.py
├── serializers.py
├── signals.py
├── urls.py
└── views.py
```

Responsibilities:

- `mapper.py`: canonical physical sensor definitions and payload normalization.
- `configuration.py`: provision definitions and bootstrap runtime configuration.
- `collector.py`: HTTP fetch, validation and persistence.
- `runtime.py`: due scheduling, status recording, backoff and locking.
- `views.py`: farm-scoped configuration/test/collect API.
- `signals.py`: creates the ingestion configuration associated with a controller where required.

## Commands

Create/update standard sensor definitions:

```powershell
python manage.py seed_sensors --device-slug <device-slug>
```

Run one collection cycle:

```powershell
python manage.py collect_sensors --once
```

Run the standalone database-configured collector loop:

```powershell
python manage.py collect_sensors
```

In the normal Docker development runtime, the background worker already collects due configurations while Django `runserver` is running.

## Unit tests

From `backend/`:

```powershell
python manage.py test sensor_ingest
```

With Docker:

```powershell
docker compose exec backend python manage.py test sensor_ingest
```

The unit tests use mocks/fixtures and are intended to validate software logic without requiring the physical Lab devices.

## Lab connectivity test

The Lab addresses are private network devices. Test them from a machine/container that can reach the LeafyAI hardware.

Water-quality endpoint:

```powershell
docker compose exec backend python -c "import requests; print(requests.get('http://192.168.1.100/readings', timeout=5).json())"
```

Ambient/water-level endpoint:

```powershell
docker compose exec backend python -c "import requests; print(requests.get('http://192.168.1.111:8080/readings', timeout=5).json())"
```

Then test the LeafyAI ingestion path:

```powershell
docker compose exec backend python manage.py collect_sensors --once
```

## Verification after collection

Recent rows can be inspected with:

```powershell
docker compose exec backend python manage.py shell -c "from telemetry.models import SensorReading; print(list(SensorReading.objects.order_by('-measured_at').values('sensor__slug','value','quality_status','measured_at')[:14]))"
```

A successful complete hardware cycle should normally provide the seven expected sensor values when all hardware validity flags are true.

## Off-Lab development

To stop the Django development server from polling physical sensors/cameras in the background:

```env
LEAFY_RUNTIME_ENABLED=false
```

This does not disable unit tests or manual management commands.

## Maintenance rules

When extending this subsystem:

- keep the seven canonical sensor slugs stable unless the wider farm-state/AI contract is deliberately migrated
- preserve hardware validity flags
- keep crop safety thresholds outside ingestion
- retain the per-controller operation lock
- test both transport failure and invalid/missing measurement behaviour
- keep physical credentials or private secrets out of tracked files
