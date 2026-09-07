# Legacy sensor prototype

This directory contains the earlier standalone sensor polling prototype. It is retained for project history/reference, but it should **not** be run alongside the Django `sensor_ingest` app.

The authoritative sensor collection path is now:

```text
ThingSpeak -> backend/sensor_ingest -> telemetry -> farm_state
```

Why it was superseded:

- the old prototype polls local owner endpoints rather than the current ThingSpeak feed;
- it depends on hard-coded Django database sensor IDs;
- it POSTs back through the REST API even when collection runs on the same Raspberry Pi;
- it does not preserve ThingSpeak `entry_id` provenance/backfill semantics;
- `SensorReading` REST endpoints are now read-only to normal API clients.

Use:

```bash
cd backend
python manage.py seed_sensors
python manage.py collect_sensors
```

See `backend/sensor_ingest/README.md` for the current design and setup.
