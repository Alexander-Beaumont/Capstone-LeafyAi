# Powerboard control

`powerboard_control` owns the TP-Link/Kasa integration for the two physical power strips assigned to each LeafyAI farm.

## Runtime contract

Each farm stores only the two physical strip addresses:

```text
Farm
└── PowerboardConfiguration
    ├── powerboard_1_ip
    └── powerboard_2_ip
```

The logical outlet mapping remains fixed in `powerboard_control/config.py`:

| Device ID | Logical device | Board | Child index |
| ---: | --- | --- | ---: |
| 1 | pH Doser | board_1 | 0 |
| 2 | EC Doser | board_1 | 1 |
| 3 | Irrigation Pump | board_1 | 2 |
| 4 | Farm Fan | board_2 | 0 |
| 5 | Light Level 1 | board_2 | 1 |
| 6 | Light Level 2 | board_2 | 2 |

Farmers therefore configure the two Powerboard IP addresses, not individual outlet IDs.

## Bootstrap behaviour

The Lab defaults remain in `.env` / `.env.example`:

```env
LEAFY_POWERBOARD_1_IP=192.168.1.102
LEAFY_POWERBOARD_2_IP=192.168.1.101
```

`bootstrap_leafy` uses these values only when it creates the initial farm's `PowerboardConfiguration` row for the first time. It uses `get_or_create(..., defaults=...)`, matching the sensor-ingestion bootstrap pattern.

After the row exists, the database is authoritative. A farmer can change either IP from Settings and a later backend/container restart does not overwrite the saved values with `.env`.

New farms do not inherit the Lab IPs. Their configuration row is created empty when the farm-scoped Powerboard settings API is first opened/saved, and the farmer supplies the two addresses.

The legacy no-`farm_id` device calls still use `.env` as a backwards-compatible fallback.

## API

Farm configuration:

```text
GET   /api/farms/{farm_id}/powerboard-config/
PATCH /api/farms/{farm_id}/powerboard-config/
```

Example PATCH:

```json
{
  "powerboard_1_ip": "192.168.1.102",
  "powerboard_2_ip": "192.168.1.101"
}
```

Hardware status/control:

```text
GET  /api/devices/?farm_id={farm_id}
POST /api/devices/{device_id}/state/
```

Example state change:

```json
{
  "state": "ON",
  "farm_id": 1
}
```

The original routes also remain valid without `farm_id` and use the environment fallback:

```text
GET  /api/devices/
POST /api/devices/{device_id}/state/   { "state": "ON" }
```

The Kasa controller confirms physical state before a state-change request is reported as successful.

## AI automatic actions

The AI policy is unchanged: only fan/light on-off decisions may be automatic after the safety layer passes. When an automatic action executes, the actuator resolves `decision.run.farm_id` to that farm's `PowerboardConfiguration`, so it cannot silently operate another farm's strips.

If a new farm has not configured its Powerboards, the farm-scoped mapping contains blank addresses and the Kasa layer returns `NOT_CONFIGURED`; it does not fall back to the Lab farm.

## Database schema

Django model/table:

```text
powerboard_control.PowerboardConfiguration
powerboard_control_powerboardconfiguration
```

Fields:

| Field | Type | Notes |
| --- | --- | --- |
| `id` | BigAutoField | Primary key |
| `farm` | OneToOne(Farm) | CASCADE; one configuration per farm |
| `powerboard_1_ip` | GenericIPAddressField | Nullable until farmer configures the farm |
| `powerboard_2_ip` | GenericIPAddressField | Nullable until farmer configures the farm |
| `updated_at` | DateTimeField | Auto-updated on save |

Migration: `powerboard_control/migrations/0001_initial.py`.

## Tests

```powershell
docker compose exec backend python manage.py test powerboard_control
docker compose exec backend python manage.py test ai_agent
```

The Powerboard test suite covers API validation plus bootstrap persistence, including the rule that farmer edits survive later bootstrap runs.

Hardware smoke test for a configured farm:

```powershell
docker compose exec backend python manage.py shell -c "from powerboard_control.runtime_config import powerboards_for_farm; from powerboard_control.bridge import get_powerboard_bridge; p=powerboards_for_farm(1); print(get_powerboard_bridge(p).get_all_device_statuses())"
```

Run hardware checks only while connected to the LeafyAI Lab network.
