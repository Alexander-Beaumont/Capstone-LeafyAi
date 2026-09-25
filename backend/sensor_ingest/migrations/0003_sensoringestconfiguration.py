import django.core.validators
import django.db.models.deletion
from django.db import migrations, models
from django.conf import settings


def bootstrap_existing_devices(apps, schema_editor):
    Configuration = apps.get_model("sensor_ingest", "SensorIngestConfiguration")
    FarmDevice = apps.get_model("telemetry", "FarmDevice")
    Sensor = apps.get_model("telemetry", "Sensor")
    selected_slug = str(settings.SENSOR_INGEST_DEVICE_SLUG or "").strip()
    poll = int(settings.SENSOR_INGEST_POLL_SECONDS)
    stale = int(settings.SENSOR_INGEST_SENSOR_STALE_SECONDS)
    for device in FarmDevice.objects.all().iterator():
        selected = bool(selected_slug and device.slug == selected_slug)
        Configuration.objects.get_or_create(
            device_id=device.id,
            defaults={
                "enabled": selected and bool(settings.LEAFY_WATER_QUALITY_URL) and bool(settings.LEAFY_AMBIENT_SENSOR_URL),
                "water_quality_url": str(settings.LEAFY_WATER_QUALITY_URL or "").strip() if selected else "",
                "ambient_sensor_url": str(settings.LEAFY_AMBIENT_SENSOR_URL or "").strip() if selected else "",
                "poll_interval_seconds": poll,
                "sensor_stale_threshold_seconds": stale,
            },
        )
        Sensor.objects.filter(device_id=device.id).update(
            expected_interval_seconds=poll,
            stale_after_seconds=stale,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("sensor_ingest", "0002_remove_legacy_ingestion_audit"),
        ("telemetry", "0014_remove_obsolete_cv_camera_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="SensorIngestConfiguration",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("enabled", models.BooleanField(default=True)),
                ("water_quality_url", models.URLField(blank=True, default="", max_length=500)),
                ("ambient_sensor_url", models.URLField(blank=True, default="", max_length=500)),
                ("poll_interval_seconds", models.PositiveIntegerField(default=30, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(86400)])),
                ("sensor_stale_threshold_seconds", models.PositiveIntegerField(default=120, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(604800)])),
                ("last_attempt_at", models.DateTimeField(blank=True, null=True)),
                ("last_success_at", models.DateTimeField(blank=True, null=True)),
                ("last_error", models.TextField(blank=True, default="")),
                ("consecutive_failures", models.PositiveIntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("device", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="sensor_ingest_configuration", to="telemetry.farmdevice")),
            ],
            options={"ordering": ["device_id"]},
        ),
        migrations.RunPython(bootstrap_existing_devices, migrations.RunPython.noop),
    ]
