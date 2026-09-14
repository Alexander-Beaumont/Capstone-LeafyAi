# FINAL LOCKED Camera API schema correction

This build corrects the prior temporary `farm_level` API rename.

## Correct contract

- Public Camera API field: `farm_level_id`
- Django model relation: `farm_level = ForeignKey(FarmLevel, ...)`
- Serializer mapping: `farm_level_id = PrimaryKeyRelatedField(source="farm_level", ...)`
- Plant Vision create/edit payloads: `farm_level_id`

No database migration is required for this correction because the Django model relationship itself is unchanged.

Example Camera create payload:

```json
{
  "farm_level_id": 1,
  "name": "Level 1 Camera",
  "position": "Top",
  "source_type": "RTSP",
  "ip_address": "192.168.1.106",
  "rtsp_port": 554,
  "rtsp_path": "/stream1",
  "enabled": true,
  "cv_enabled": true,
  "capture_interval_minutes": 30
}
```

Zero-Camera startup behavior is unchanged: the example above is only submitted after a user chooses **Add Camera**.
