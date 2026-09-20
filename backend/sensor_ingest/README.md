# Leafy AI sensor_ingest

`sensor_ingest` is the integration boundary between the physical LeafyAI farm sensors and Leafy AI's internal Django database.

It deliberately **does not** decide whether the farm is healthy or whether hardware should run. It retrieves, validates, normalises and stores physical sensor observations.

Operational interpretation belongs to `farm_state`, the safety layer and the AI/VLM layer.

The current implementation communicates directly with the physical farm devices over the local network.

ThingSpeak is no longer part of the sensor-ingestion architecture.

---

## Data contract

The current physical farm devices are mapped as follows:

| Device | Payload field | Leafy AI storage |
| --- | --- | --- |
| Water-quality sensor | `ph` | `SensorReading` (`water_ph`) |
| Water-quality sensor | `ec` | `SensorReading` (`electrical_conductivity`) |
| Water-quality sensor | `water_temperature_c` | `SensorReading` (`water_temperature`) |
| Ambient sensor | `ambient_temperature_c` | `SensorReading` (`ambient_temperature`) |
| Ambient sensor | `humidity_percent` | `SensorReading` (`relative_humidity`) |
| Ambient sensor | `dew_point_c` | `SensorReading` (`dew_point`) |
| Ambient / level sensor | `water_level` | `SensorReading` (`reservoir_water_level`) |

The mapping is version-controlled in:

```text
sensor_ingest/services/mapper.py
```

It should not be made editable from the frontend because an incorrect mapping could mislabel physical farm data.

The current sensor definitions are:

```text
water_ph
electrical_conductivity
water_temperature
ambient_temperature
relative_humidity
dew_point
reservoir_water_level
```

---

## Physical sensor endpoints

The currently tested LeafyAI Lab devices are:

```text
Water-quality sensor:
http://192.168.1.100/readings
```

```text
Ambient / water-level sensor:
http://192.168.1.111:8080/readings
```

These addresses are private Lab-network addresses.

They are expected to be unreachable when the developer is outside the LeafyAI Lab network.

A connection failure to these IP addresses outside the Lab does not by itself indicate a backend defect.

---

## Reliability properties

The current implementation:

- Reads physical sensor data directly over local HTTP.
- Uses configurable HTTP timeout and retry behaviour.
- Fetches the water-quality and ambient devices independently.
- Does not require one device to succeed before processing valid observations from the other.
- Uses hardware validity flags where available.
- Performs basic physical-range validation.
- Stores valid observations in `telemetry.SensorReading`.
- Keeps source measurement time separate from Django receipt time where provided.
- Allows physically valid but crop-unsafe values to remain in history.
- Leaves crop safety and operational interpretation to `farm_state`, safety logic and the AI/VLM layer.
- Uses persisted sensor readings as the source of truth for downstream farm-state calculations.

The ingestion layer should remain focused on physical data acquisition and normalization.

---

## Quality status

The local physical devices expose validity information that is used by the mapper.

Relevant validity flags include:

```text
ph_valid
ec_valid
water_temperature_valid
ambient_valid
water_level_valid
```

Valid physical observations are normally stored as:

```text
quality_status = valid
source = local_http
```

Physically impossible values detected by the mapper may be stored as:

```text
quality_status = suspect
```

A real measurement that is unsafe for the crop must not be deleted by the ingestion layer.

For example, a pH value can still be a valid physical measurement even if it is outside the desired crop operating range.

Crop-specific interpretation belongs to:

```text
farm_state
safety logic
AI/VLM layer
```

---

## Active architecture

The current ingestion flow is:

```text
Water-quality device
192.168.1.100/readings
        |
        | HTTP
        v
  SensorCollector
        |
        +---- water_ph
        +---- electrical_conductivity
        +---- water_temperature
        |
        v

Ambient / level device
192.168.1.111:8080/readings
        |
        | HTTP
        v
  SensorCollector
        |
        +---- ambient_temperature
        +---- relative_humidity
        +---- dew_point
        +---- reservoir_water_level
        |
        v

telemetry.SensorReading
        |
        v
farm_state
        |
        v
REST API
        |
        v
Frontend / AI layer
```

There is one active physical sensor-ingestion path:

```text
Physical sensors
    -> SensorCollector
    -> mapper
    -> SensorReading
```

Do not add another parallel sensor provider unless the architecture is intentionally changed by the team.

---

## Important files

The active sensor-ingestion files are:

```text
sensor_ingest/
├── management/
│   └── commands/
│       ├── collect_sensors.py
│       └── seed_sensors.py
├── migrations/
│   ├── 0001_initial.py
│   └── 0002_remove_legacy_ingestion_audit.py
├── services/
│   ├── collector.py
│   └── mapper.py
├── apps.py
├── exceptions.py
├── models.py
└── README.md
```

### `services/collector.py`

Responsibilities:

- Connect to both local physical sensor endpoints.
- Apply HTTP timeout and retry behaviour.
- Retrieve device payloads.
- Pass payloads to the mapper.
- Persist normalized observations.

### `services/mapper.py`

Responsibilities:

- Map physical payload fields to LeafyAI sensor definitions.
- Read hardware validity flags.
- Validate numeric values.
- Apply basic physical-range checks.
- Produce normalized readings.

### `management/commands/collect_sensors.py`

Responsibilities:

- Run one physical collection cycle.
- Run continuous polling.
- Respect the configured polling interval.

### `management/commands/seed_sensors.py`

Responsibilities:

- Create or update the seven sensor definitions for an existing `FarmDevice`.

For a complete fresh system setup, use:

```text
bootstrap_leafy
```

instead.

---

## Removed legacy components

The previous ThingSpeak ingestion path has been removed.

The following components are no longer part of the active architecture:

```text
sensor_ingest/clients/thingspeak.py
sensor_ingest/services/parser.py
sensor_ingest/services/ingestion.py
sensor_ingest/services/health.py
sensor_ingest/serializers.py
sensor_ingest/urls.py
sensor_ingest/views.py
```

The related legacy tests were also removed:

```text
sensor_ingest/tests/test_thingspeak_client.py
sensor_ingest/tests/test_parser.py
sensor_ingest/tests/test_ingestion.py
sensor_ingest/tests/test_health_api.py
```

The following ThingSpeak-era behaviour is no longer required:

```text
ThingSpeak API access
ThingSpeak API keys
ThingSpeak entry_id tracking
payload SHA-256 ingestion audit
historical backfill
periodic reconciliation
ThingSpeak health endpoint
provider switching
ThingSpeak pump-state ingestion
ThingSpeak target-EC ingestion
```

Do not reintroduce these components unless the team intentionally changes the ingestion architecture.

---

## Legacy database migration

The following migration files must remain in the repository:

```text
sensor_ingest/migrations/0001_initial.py
sensor_ingest/migrations/0002_remove_legacy_ingestion_audit.py
```

Do not delete `0002_remove_legacy_ingestion_audit.py`.

It removes the previous legacy models:

```text
IngestionRecord
IngestionSourceState
```

from databases that were created using the older ingestion design.

This migration allows existing databases to move safely to the new local-sensor architecture.

---

## Configuration

For the current local development workflow, the backend reads the repository-root:

```text
.env.example
```

directly.

A separate `.env` file is not required unless the project configuration is intentionally changed.

The relevant sensor configuration is:

```env
SENSOR_INGEST_DEVICE_SLUG=test-device

LEAFY_WATER_QUALITY_URL=http://192.168.1.100/readings
LEAFY_AMBIENT_SENSOR_URL=http://192.168.1.111:8080/readings

SENSOR_INGEST_POLL_SECONDS=30
SENSOR_INGEST_EXPECTED_INTERVAL_SECONDS=30
SENSOR_INGEST_SENSOR_STALE_SECONDS=120

SENSOR_INGEST_HTTP_TIMEOUT_SECONDS=5
SENSOR_INGEST_HTTP_RETRY_TOTAL=4
SENSOR_INGEST_HTTP_RETRY_BACKOFF=0.5

SENSOR_INGEST_FAILURE_BACKOFF_BASE_SECONDS=5
SENSOR_INGEST_FAILURE_BACKOFF_MAX_SECONDS=300

SENSOR_INGEST_LOG_LEVEL=INFO
```

System or process environment variables can override these values.

Do not commit real API keys, passwords or other secrets into `.env.example`.

---

## One-time local setup

### Windows PowerShell

From the repository root:

```powershell
python -m venv .venv
```

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r .\backend\requirements.txt
```

Enter the backend directory:

```powershell
cd backend
```

Apply database migrations:

```powershell
python manage.py migrate
```

Bootstrap the LeafyAI configuration:

```powershell
python manage.py bootstrap_leafy
```

`bootstrap_leafy` creates or updates the configured:

```text
Farm
FarmDevice
7 sensor definitions
FarmLevel
Camera configuration
```

where applicable.

---

## Local test without farm hardware

The physical sensors use local `192.168.1.x` addresses.

When testing outside the Lab, disable the background hardware runtime:

```powershell
$env:LEAFY_RUNTIME_ENABLED="false"
```

Run the Django system check:

```powershell
python manage.py check
```

Run the relevant backend tests:

```powershell
python manage.py test sensor_ingest telemetry farm_state
```

The Django server can then be started without attempting the physical background runtime:

```powershell
python manage.py runserver 0.0.0.0:8000 --noreload
```

Expected startup output includes:

```text
Leafy AI background runtime disabled by LEAFY_RUNTIME_ENABLED.
System check identified no issues (0 silenced).
```

To restore the configured runtime behaviour:

```powershell
Remove-Item Env:LEAFY_RUNTIME_ENABLED
```

---

## Lab hardware test

The physical collection test must be run while connected to the LeafyAI Lab network.

Activate the local virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Enter the backend:

```powershell
cd backend
```

Ensure migrations and bootstrap data are ready:

```powershell
python manage.py migrate
python manage.py bootstrap_leafy
```

Run one physical sensor collection cycle:

```powershell
python manage.py collect_sensors --once
```

Expected successful output:

```text
Local sensor cycle stored 7 reading(s); missing=[] invalid=[]
Sensor cycle complete: stored=7 reading(s).
```

This confirms that both physical sensor devices were reachable and all seven expected observations were persisted.

---

## Verify stored readings

The latest readings can be inspected from the Django shell.

Run:

```powershell
python manage.py shell
```

Then:

```python
from telemetry.models import SensorReading
from django.utils import timezone

for reading in (
    SensorReading.objects
    .select_related("sensor")
    .order_by("-measured_at")[:7]
):
    print(
        reading.sensor.slug,
        reading.value,
        reading.sensor.unit,
        reading.quality_status,
        timezone.localtime(reading.measured_at),
    )
```

Expected sensor slugs:

```text
water_ph
electrical_conductivity
water_temperature
ambient_temperature
relative_humidity
dew_point
reservoir_water_level
```

Valid local hardware observations should normally show:

```text
quality_status = valid
source = local_http
```

---

## Continuous collection

Run the collector continuously with:

```powershell
python manage.py collect_sensors
```

Run one cycle only:

```powershell
python manage.py collect_sensors --once
```

Override the configured polling interval:

```powershell
python manage.py collect_sensors --poll-seconds 10
```

The normal LeafyAI background runtime can also run sensor collection when:

```env
LEAFY_RUNTIME_ENABLED=true
```

Do not use the old ThingSpeak options:

```text
--no-backfill
--backfill
--reconcile-seconds
```

They are not part of the current local HTTP architecture.

---

## Farm state

`sensor_ingest` does not directly decide farm health and does not directly control hardware.

Persisted readings are consumed by `farm_state`.

The intended flow is:

```text
Physical sensor
      |
      v
SensorCollector
      |
      v
SensorReading
      |
      v
farm_state
      |
      v
REST API / frontend / AI
```

`farm_state` is responsible for exposing and aggregating information such as:

- stable sensor slug and type
- current value and unit
- source measurement time
- receipt time
- reading quality
- reading age/freshness
- recent trend information

The current deterministic trend window is configured by:

```env
FARM_STATE_SENSOR_TREND_WINDOW_MINUTES=30
```

The old ThingSpeak-derived irrigation-pump state and external target-EC setpoint are no longer part of this sensor-ingestion feed.

Powerboard state is handled independently by the powerboard subsystem.

---

## Time handling

Django stores timestamps using timezone-aware UTC values.

Do not manually store Melbourne local time in the database.

For display or debugging, use Django timezone conversion:

```python
from django.utils import timezone

timezone.localtime(reading.measured_at)
```

The application timezone is configured as:

```text
Australia/Melbourne
```

This allows daylight-saving behaviour to be handled correctly.

---

## Runtime files

The following files and directories are generated locally and must not be committed:

```text
.venv/
.env
backend/db.sqlite3
backend/media/
__pycache__/
*.pyc
```

They should be covered by the repository `.gitignore`.

The local SQLite database can be recreated with:

```powershell
python manage.py migrate
python manage.py bootstrap_leafy
```

Generated camera media is recreated when new images are captured and stored.

---

## Tests

Local unit/integration tests do not require the real farm hardware when the physical background runtime is disabled.

Run:

```powershell
$env:LEAFY_RUNTIME_ENABLED="false"
python manage.py test sensor_ingest telemetry farm_state
```

Physical sensor connectivity must be verified separately in the Lab using:

```powershell
python manage.py collect_sensors --once
```

The two tests serve different purposes:

```text
Local tests
    -> verify backend logic

Lab collection test
    -> verify real network and physical sensor integration
```

---

## Handover checklist

Before merging sensor-ingestion changes, confirm:

- [ ] ThingSpeak runtime code has not been reintroduced.
- [ ] `SensorCollector` remains the single physical ingestion path.
- [ ] The two local sensor endpoints are configured correctly.
- [ ] All seven sensor definitions are present.
- [ ] `dew_point` remains included.
- [ ] Hardware validity flags are still respected.
- [ ] Valid observations are stored with `source=local_http`.
- [ ] `0002_remove_legacy_ingestion_audit.py` remains in the migration history.
- [ ] `farm_state` still consumes persisted `SensorReading` data.
- [ ] No ThingSpeak health API is exposed.
- [ ] No ThingSpeak backfill or reconciliation options remain.
- [ ] Local testing works with `LEAFY_RUNTIME_ENABLED=false`.
- [ ] `python manage.py check` passes.
- [ ] Backend tests pass.
- [ ] Lab testing stores all seven readings using `collect_sensors --once`.
- [ ] `.venv`, `db.sqlite3`, media and Python cache files are not committed.

---

## Final handover state

The current expected architecture is:

```text
LeafyAI physical sensors
        |
        | Local HTTP
        v
SensorCollector
        |
        v
Sensor mapper / validation
        |
        v
telemetry.SensorReading
        |
        v
farm_state
        |
        v
LeafyAI REST API / frontend / AI layer
```

ThingSpeak is not required.

A provider-switching layer is not required.

The local HTTP implementation has been tested successfully against the physical LeafyAI farm sensor system.
