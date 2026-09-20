# Sensor ingestion

`sensor_ingest` reads LeafyAI's physical sensors directly over the local network and stores observations in `telemetry.SensorReading`. There is no ThingSpeak/cloud ingestion path.

## Physical sources

| Local endpoint | Payload keys | LeafyAI sensor slugs |
| --- | --- | --- |
| `LEAFY_WATER_QUALITY_URL` | `ph`, `ec`, `water_temperature_c` | `water_ph`, `electrical_conductivity`, `water_temperature` |
| `LEAFY_AMBIENT_SENSOR_URL` | `ambient_temperature_c`, `humidity_percent`, `dew_point_c`, `water_level` | `ambient_temperature`, `relative_humidity`, `dew_point`, `reservoir_water_level` |

The current lab defaults are configured through the repository `.env`, for example:

```env
LEAFY_WATER_QUALITY_URL=http://192.168.1.100/readings
LEAFY_AMBIENT_SENSOR_URL=http://192.168.1.111:8080/readings
SENSOR_INGEST_DEVICE_SLUG=test-device
SENSOR_INGEST_POLL_SECONDS=30
SENSOR_INGEST_EXPECTED_INTERVAL_SECONDS=30
SENSOR_INGEST_SENSOR_STALE_SECONDS=120
SENSOR_INGEST_HTTP_TIMEOUT_SECONDS=5
SENSOR_INGEST_HTTP_RETRY_TOTAL=4
SENSOR_INGEST_HTTP_RETRY_BACKOFF=0.5
SENSOR_INGEST_FAILURE_BACKOFF_BASE_SECONDS=5
SENSOR_INGEST_FAILURE_BACKOFF_MAX_SECONDS=300
```

## Commands

Create/update the seven physical sensor definitions:

```bash
python manage.py seed_sensors
```

Collect one cycle:

```bash
python manage.py collect_sensors --once
```

Run continuously (the Django background runtime also starts this command):

```bash
python manage.py collect_sensors
```

The collector respects the device-provided validity flags. Valid values are stored with `quality_status=valid`; basic physically impossible values are retained as `suspect`; readings explicitly marked invalid by hardware are not stored.
