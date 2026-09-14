# Leafy AI sensor_ingest

`sensor_ingest` is the integration boundary between the project owner's external ThingSpeak telemetry channel and Leafy AI's internal Django database.

It deliberately **does not** decide whether the farm is healthy or whether hardware should run. It only retrieves, validates, normalises, deduplicates, stores and monitors externally sourced observations. Operational interpretation belongs to `farm_state` and the safety/AI layers.

## Data contract

The current owner-provided ThingSpeak channel is mapped as follows:

| ThingSpeak field | Meaning | Leafy AI storage |
|---|---|---|
| `field1` | Water pH | `SensorReading` (`water_ph`) |
| `field2` | Electrical conductivity (µS/cm) | `SensorReading` (`electrical_conductivity`) |
| `field3` | Water temperature (°C) | `SensorReading` (`water_temperature`) |
| `field4` | Ambient temperature (°C) | `SensorReading` (`ambient_temperature`) |
| `field5` | Relative humidity (%) | `SensorReading` (`relative_humidity`) |
| `field6` | Reservoir water level (cm) | `SensorReading` (`reservoir_water_level`) |
| `field7` | Irrigation pump status (`0`/`1`) | `ActuatorStateObservation` |
| `field8` | Target EC (µS/cm) | `SetpointObservation` |

The field mapping is version-controlled in `services/mapper.py`. It is intentionally not editable from the dashboard because a field-mapping mistake could mislabel physical farm data.

## Reliability properties

- Uses the ThingSpeak read API over HTTPS.
- Sends the private read API key in the `THINGSPEAKAPIKEY` header rather than the URL.
- Separates source measurement time (`measured_at`) from Leafy AI receipt time (`received_at`).
- Uses ThingSpeak `entry_id` for source identity.
- Stores an ingestion audit record and payload SHA-256 for every processed entry.
- Repeated polling/backfill is idempotent.
- Reuse of the same entry ID with changed payload content raises a conflict; history is not overwritten.
- Missing/invalid individual fields do not discard other valid fields in the entry.
- Potentially unsafe crop values are still retained as historical observations. The ingestion layer only flags structurally/physically suspect values; crop safety is handled later.
- Startup backfill reconciles recent history after Pi/network outages.
- Periodic reconciliation self-heals missed entries.
- HTTP connection health and source-data freshness are tracked separately.
- Sensor-reading APIs are read-only to normal REST clients; trusted ingestion writes through the Django ORM internally.

## One-time setup

1. Copy `.env.example` to `.env` at repository root and set the ThingSpeak channel/key and `SENSOR_INGEST_DEVICE_SLUG`.
2. Apply migrations:

   ```bash
   cd backend
   python manage.py migrate
   ```

3. Confirm the desired `FarmDevice.slug`. Existing devices receive stable slugs during migration. You can inspect them with:

   ```bash
   python manage.py shell -c "from telemetry.models import FarmDevice; print(list(FarmDevice.objects.values('id','name','slug')))"
   ```

4. Set `SENSOR_INGEST_DEVICE_SLUG` to that slug and seed the six sensor definitions:

   ```bash
   python manage.py seed_sensors
   ```

5. Validate with a single collection:

   ```bash
   python manage.py collect_sensors --once
   ```

## Continuous collection

Development:

```bash
python manage.py collect_sensors
```

Useful options:

```bash
python manage.py collect_sensors --once
python manage.py collect_sensors --once --no-backfill
python manage.py collect_sensors --backfill 100
python manage.py collect_sensors --poll-seconds 30 --reconcile-seconds 300
```

The production Raspberry Pi should run the command as a separate process (for example the supplied systemd service). Do **not** start the collector from `AppConfig.ready()` or a Django web request, because multiple web workers/autoreload processes can start duplicate collectors.

## Health API

Authenticated users can query:

```text
GET /api/sensor-ingest/health/
```

The response distinguishes:

- `connection_status`: can Leafy AI reach ThingSpeak?
- `feed_status`: is the newest source measurement recent enough?

This prevents an HTTP `200 OK` from being mistaken for fresh physical telemetry.

## Quality status

ThingSpeak values default to `unverified` because the current eight-field feed does not expose the project-owner ESP32 validity flags. Basic impossible values such as pH outside 0–14 or humidity outside 0–100% are retained but marked `suspect`.

A real but crop-unsafe value (for example pH outside basil's safe operating range) must **not** be deleted by ingestion. It remains history and is handled by the farm-state/safety layers.

## Farm state

`farm_state` now exposes:

- stable sensor slug/type
- current value/unit
- source measurement and receipt times
- source/provenance identifiers
- quality status
- sensor-specific freshness
- a deterministic recent trend summary (count, mean, min, max, change and direction)
- latest observed irrigation-pump state
- latest external target-EC setpoint

Raw ThingSpeak history is not sent directly to the LLM.

## Tests

Run:

```bash
python manage.py test sensor_ingest telemetry farm_state
```

Tests use mocked/fixed payloads and do not require the real farm, internet access or a real API key.
