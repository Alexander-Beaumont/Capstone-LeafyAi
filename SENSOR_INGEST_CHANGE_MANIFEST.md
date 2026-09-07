# Sensor Ingest Implementation — File Manifest

This manifest describes the complete ThingSpeak ingestion implementation added to the supplied `Capstone-LeafyAi-main (2).zip` project. The original uploaded ZIP was not modified.

## New Django app: `backend/sensor_ingest/`

| File | Purpose |
|---|---|
| `backend/sensor_ingest/__init__.py` | Python package marker. |
| `backend/sensor_ingest/apps.py` | Django app configuration. |
| `backend/sensor_ingest/exceptions.py` | Typed transport, payload, configuration and conflict exceptions. |
| `backend/sensor_ingest/models.py` | External-source operational health (`IngestionSourceState`) and per-entry audit/idempotency record (`IngestionRecord`). |
| `backend/sensor_ingest/admin.py` | Read-only Django admin views for ingestion health/audit history. |
| `backend/sensor_ingest/serializers.py` | Read-only DRF serializers for source state and ingestion records. |
| `backend/sensor_ingest/views.py` | Read-only audit/source endpoints and computed health endpoint. |
| `backend/sensor_ingest/urls.py` | `/api/sensor-ingest/...` routes. |
| `backend/sensor_ingest/migrations/0001_initial.py` | Creates the ingestion source/audit tables. |
| `backend/sensor_ingest/clients/thingspeak.py` | Isolated ThingSpeak HTTPS client, header-based read key, retries/timeouts and access-error handling. |
| `backend/sensor_ingest/services/parser.py` | Validates entry ID/timestamp and creates deterministic payload hashes. |
| `backend/sensor_ingest/services/mapper.py` | Version-controlled field1–field8 mapping and per-field normalization/quality handling. |
| `backend/sensor_ingest/services/ingestion.py` | Atomic/idempotent ORM persistence and conflict detection. |
| `backend/sensor_ingest/services/collector.py` | Coordinates latest polling, history reconciliation/backfill and source health. |
| `backend/sensor_ingest/services/health.py` | Separates collector heartbeat, HTTP connection state and physical-feed freshness. |
| `backend/sensor_ingest/management/commands/seed_sensors.py` | Reproducibly creates the six physical sensor definitions by stable slug. |
| `backend/sensor_ingest/management/commands/collect_sensors.py` | Continuous collector daemon plus `--once`, backfill and reconciliation options. |
| `backend/sensor_ingest/README.md` | Architecture, data contract, setup, operations and test documentation. |
| `backend/sensor_ingest/tests/fixtures.py` | Deterministic ThingSpeak payload fixtures. |
| `backend/sensor_ingest/tests/test_parser.py` | Source identity/timestamp/hash tests. |
| `backend/sensor_ingest/tests/test_mapper.py` | Field mapping, partial data and quality tests. |
| `backend/sensor_ingest/tests/test_thingspeak_client.py` | HTTP/header/access-response tests without live internet. |
| `backend/sensor_ingest/tests/test_ingestion.py` | Persistence, idempotency, conflict and partial-entry tests. |
| `backend/sensor_ingest/tests/test_collector.py` | Latest/backfill/configuration tests. |
| `backend/sensor_ingest/tests/test_health_api.py` | Operational health API test. |
| `backend/sensor_ingest/tests/test_seed_command.py` | Repeatable sensor seeding test. |
| package `__init__.py` files | Package markers for clients/services/management/migrations/tests. |

## Changed telemetry/domain files

| File | Change |
|---|---|
| `backend/telemetry/models.py` | Added stable `FarmDevice.slug` and `Sensor.slug`; sensor timing/enabled metadata; split `SensorReading.measured_at`/`received_at`; added source-entry provenance and quality; added `ActuatorStateObservation` for ThingSpeak field 7 and `SetpointObservation` for field 8. |
| `backend/telemetry/migrations/0010_sensor_ingest_support.py` | Backwards-compatible schema/data migration. Existing device/sensor slugs are populated and existing sensor timestamps are copied into `measured_at`. |
| `backend/telemetry/serializers.py` | Exposes new sensor/provenance fields and adds read-only actuator/setpoint observation serializers. |
| `backend/telemetry/views.py` | Makes historical sensor/actuator/setpoint observations read-only through REST. |
| `backend/telemetry/urls.py` | Adds read-only actuator/setpoint observation routes. |
| `backend/telemetry/admin.py` | Adds admin visibility while keeping historical observations non-editable through admin. |
| `backend/telemetry/tests.py` | Updated for stable slugs, source timestamps/provenance and read-only history API. |

## Changed farm-state files

| File | Change |
|---|---|
| `backend/farm_state/services.py` | Uses source `measured_at`; honours per-sensor stale thresholds; exposes provenance/quality; calculates deterministic 30-minute trends; includes latest observed pump state and target EC. |
| `backend/farm_state/thresholds.py` | Clarifies the old one-hour threshold is only a fallback. |
| `backend/farm_state/tests.py` | Tests measured-time freshness, sensor-specific staleness and trend direction. |

## Changed backend/project configuration

| File | Change |
|---|---|
| `backend/core/settings.py` | Registers `sensor_ingest`; loads root `.env`; adds ThingSpeak/collector/backfill/retry/freshness/trend settings; adds focused ingestion logging; makes host/CORS configuration environment-driven. |
| `backend/core/urls.py` | Includes `sensor_ingest` routes. |
| `.env.example` | Adds placeholders/settings for ThingSpeak and collector operation. No real credentials are included. |
| `docker-compose.yml` | Adds a dedicated `sensor_ingest` worker process and passes root environment settings to the backend/worker. |

## Documentation/deployment additions

| File | Purpose |
|---|---|
| `database_schema_v2.md` | Updated schema documentation for stable IDs, provenance, field 7/8 observations and ingestion audit tables. |
| `Sensors/README.md` | Marks the old standalone sensor poller as a legacy prototype so it is not run alongside the new collector. |
| `deployment/systemd/leafyai-sensor-ingest.service.example` | Raspberry Pi service-manager example for automatic startup/restart. |
| `SENSOR_INGEST_CHANGE_MANIFEST.md` | This file. |

## ThingSpeak mapping implemented

| Field | Meaning | Internal representation |
|---|---|---|
| 1 | Water pH | `SensorReading` / `water_ph`, type `ph`, `pH` |
| 2 | Electrical conductivity | `SensorReading` / `electrical_conductivity`, type `ec`, `µS/cm` |
| 3 | Water temperature | `SensorReading` / `water_temperature`, type `water_temperature`, `°C` |
| 4 | Ambient temperature | `SensorReading` / `ambient_temperature`, type `ambient_temperature`, `°C` |
| 5 | Relative humidity | `SensorReading` / `relative_humidity`, type `humidity`, `%` |
| 6 | Reservoir water level | `SensorReading` / `reservoir_water_level`, type `water_level`, `cm` |
| 7 | Irrigation pump status | `ActuatorStateObservation` / `irrigation_pump` |
| 8 | Target EC | `SetpointObservation` / `target_ec`, `µS/cm` |

The canonical `sensor_type` values intentionally match the existing AI safety configuration (`ph`, `ec`, `water_temperature`, `ambient_temperature`, `humidity`, `water_level`).

## First-run commands

After merging/copying these changes into the real team repository:

```bash
cd backend
python -m pip install -r requirements.txt
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py migrate
```

Inspect the device slugs created by the migration:

```bash
python manage.py shell -c "from telemetry.models import FarmDevice; print(list(FarmDevice.objects.values('id','name','slug')))"
```

Set the desired slug in the repository-root `.env`, then:

```bash
python manage.py seed_sensors
python manage.py collect_sensors --once
python manage.py test sensor_ingest telemetry farm_state
```

For continuous development operation:

```bash
python manage.py collect_sensors
```

The old top-level `Sensors/main.py` process should not be running at the same time.

## Verification performed in the artifact-building environment

- Every Python file in `backend/` passes `python -m compileall` syntax compilation.
- No unresolved Git conflict markers were found in the patched backend.
- The project was inspected for stale `SensorReading.timestamp` application references after the schema rename; runtime code now uses `measured_at`/`received_at`.
- Live Django migration/test execution could not be completed in the artifact-building container because the container has no Django installation and outbound package installation is unavailable. The supplied tests are therefore intended to be run immediately in the project's existing virtual environment using the commands above.
