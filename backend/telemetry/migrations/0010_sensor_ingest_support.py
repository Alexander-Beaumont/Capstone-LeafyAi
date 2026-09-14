from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
from django.utils.text import slugify


def populate_identifiers_and_measurement_times(apps, schema_editor):
    FarmDevice = apps.get_model("telemetry", "FarmDevice")
    Sensor = apps.get_model("telemetry", "Sensor")
    SensorReading = apps.get_model("telemetry", "SensorReading")

    used_device_slugs = set()
    for device in FarmDevice.objects.all().order_by("id"):
        base = (slugify(device.name or "") or "device")[:70].rstrip("-_") or "device"
        candidate = base
        suffix = 2
        while candidate in used_device_slugs:
            candidate = f"{base}-{suffix}"
            suffix += 1
        device.slug = candidate
        device.save(update_fields=["slug"])
        used_device_slugs.add(candidate)

    used_sensor_slugs = {}
    for sensor in Sensor.objects.all().order_by("device_id", "id"):
        base = (slugify(sensor.sensor_type or "") or "sensor")[:70].rstrip("-_") or "sensor"
        used = used_sensor_slugs.setdefault(sensor.device_id, set())
        candidate = base
        suffix = 2
        while candidate in used:
            candidate = f"{base}-{suffix}"
            suffix += 1
        sensor.slug = candidate
        sensor.save(update_fields=["slug"])
        used.add(candidate)

    for reading in SensorReading.objects.all().only("id", "received_at"):
        reading.measured_at = reading.received_at
        reading.save(update_fields=["measured_at"])


class Migration(migrations.Migration):
    dependencies = [
        ("telemetry", "0009_remove_cameraimage_timestamp_cameraimage_captured_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="farmdevice",
            name="slug",
            field=models.SlugField(blank=True, max_length=80, null=True),
        ),
        migrations.AddField(
            model_name="sensor",
            name="slug",
            field=models.SlugField(blank=True, max_length=80, null=True),
        ),
        migrations.AddField(
            model_name="sensor",
            name="enabled",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="sensor",
            name="expected_interval_seconds",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="sensor",
            name="stale_after_seconds",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.RenameField(
            model_name="sensorreading",
            old_name="timestamp",
            new_name="received_at",
        ),
        migrations.AlterField(
            model_name="sensorreading",
            name="value",
            field=models.DecimalField(decimal_places=4, max_digits=12),
        ),
        migrations.AddField(
            model_name="sensorreading",
            name="measured_at",
            field=models.DateTimeField(db_index=True, null=True),
        ),
        migrations.AddField(
            model_name="sensorreading",
            name="source",
            field=models.CharField(default="manual", max_length=50),
        ),
        migrations.AddField(
            model_name="sensorreading",
            name="source_channel_id",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
        migrations.AddField(
            model_name="sensorreading",
            name="source_entry_id",
            field=models.PositiveBigIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="sensorreading",
            name="quality_status",
            field=models.CharField(
                choices=[
                    ("valid", "Valid"),
                    ("unverified", "Unverified"),
                    ("suspect", "Suspect"),
                ],
                default="unverified",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="sensorreading",
            name="quality_notes",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.RunPython(
            populate_identifiers_and_measurement_times,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="farmdevice",
            name="slug",
            field=models.SlugField(blank=True, max_length=80, unique=True),
        ),
        migrations.AlterField(
            model_name="sensor",
            name="slug",
            field=models.SlugField(blank=True, max_length=80),
        ),
        migrations.AlterField(
            model_name="sensorreading",
            name="measured_at",
            field=models.DateTimeField(
                db_index=True,
                default=django.utils.timezone.now,
            ),
        ),
        migrations.AddConstraint(
            model_name="sensor",
            constraint=models.UniqueConstraint(
                fields=("device", "slug"),
                name="unique_sensor_slug_per_device",
            ),
        ),
        migrations.AddIndex(
            model_name="sensorreading",
            index=models.Index(
                fields=["sensor", "measured_at"],
                name="sensor_measured_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="sensorreading",
            constraint=models.UniqueConstraint(
                fields=(
                    "sensor",
                    "source",
                    "source_channel_id",
                    "source_entry_id",
                ),
                name="unique_external_sensor_reading",
            ),
        ),
        migrations.CreateModel(
            name="ActuatorStateObservation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("actuator_slug", models.SlugField(max_length=80)),
                (
                    "state",
                    models.CharField(
                        choices=[("off", "Off"), ("on", "On")],
                        max_length=10,
                    ),
                ),
                ("measured_at", models.DateTimeField(db_index=True)),
                ("received_at", models.DateTimeField(auto_now_add=True)),
                ("source", models.CharField(default="manual", max_length=50)),
                (
                    "source_channel_id",
                    models.CharField(blank=True, default="", max_length=100),
                ),
                (
                    "source_entry_id",
                    models.PositiveBigIntegerField(blank=True, null=True),
                ),
                (
                    "quality_status",
                    models.CharField(
                        choices=[
                            ("valid", "Valid"),
                            ("unverified", "Unverified"),
                            ("suspect", "Suspect"),
                        ],
                        default="unverified",
                        max_length=20,
                    ),
                ),
                (
                    "quality_notes",
                    models.CharField(blank=True, default="", max_length=255),
                ),
                (
                    "device",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="actuator_state_observations",
                        to="telemetry.farmdevice",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="SetpointObservation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("setpoint_slug", models.SlugField(max_length=80)),
                ("value", models.DecimalField(decimal_places=4, max_digits=12)),
                ("unit", models.CharField(max_length=50)),
                ("measured_at", models.DateTimeField(db_index=True)),
                ("received_at", models.DateTimeField(auto_now_add=True)),
                ("source", models.CharField(default="manual", max_length=50)),
                (
                    "source_channel_id",
                    models.CharField(blank=True, default="", max_length=100),
                ),
                (
                    "source_entry_id",
                    models.PositiveBigIntegerField(blank=True, null=True),
                ),
                (
                    "quality_status",
                    models.CharField(
                        choices=[
                            ("valid", "Valid"),
                            ("unverified", "Unverified"),
                            ("suspect", "Suspect"),
                        ],
                        default="unverified",
                        max_length=20,
                    ),
                ),
                (
                    "quality_notes",
                    models.CharField(blank=True, default="", max_length=255),
                ),
                (
                    "device",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="setpoint_observations",
                        to="telemetry.farmdevice",
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="actuatorstateobservation",
            index=models.Index(
                fields=["device", "actuator_slug", "measured_at"],
                name="actuator_obs_time_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="actuatorstateobservation",
            constraint=models.UniqueConstraint(
                fields=(
                    "device",
                    "actuator_slug",
                    "source",
                    "source_channel_id",
                    "source_entry_id",
                ),
                name="uniq_external_actuator_obs",
            ),
        ),
        migrations.AddIndex(
            model_name="setpointobservation",
            index=models.Index(
                fields=["device", "setpoint_slug", "measured_at"],
                name="setpoint_obs_time_idx",
            ),
        ),
        migrations.AddConstraint(
            model_name="setpointobservation",
            constraint=models.UniqueConstraint(
                fields=(
                    "device",
                    "setpoint_slug",
                    "source",
                    "source_channel_id",
                    "source_entry_id",
                ),
                name="uniq_external_setpoint_obs",
            ),
        ),
    ]
