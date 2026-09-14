from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("telemetry", "0010_sensor_ingest_support"),
    ]

    operations = [
        migrations.CreateModel(
            name="IngestionSourceState",
            fields=[
                (
                    "key",
                    models.SlugField(max_length=80, primary_key=True, serialize=False),
                ),
                ("provider", models.CharField(max_length=50)),
                ("external_source_id", models.CharField(max_length=100)),
                ("last_attempt_at", models.DateTimeField(blank=True, null=True)),
                (
                    "last_http_success_at",
                    models.DateTimeField(blank=True, null=True),
                ),
                ("last_new_entry_at", models.DateTimeField(blank=True, null=True)),
                (
                    "last_source_entry_id",
                    models.PositiveBigIntegerField(blank=True, null=True),
                ),
                (
                    "last_source_measured_at",
                    models.DateTimeField(blank=True, null=True),
                ),
                ("consecutive_failures", models.PositiveIntegerField(default=0)),
                (
                    "last_error_code",
                    models.CharField(blank=True, default="", max_length=100),
                ),
                ("last_error_message", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="IngestionRecord",
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
                ("source_entry_id", models.PositiveBigIntegerField()),
                ("source_measured_at", models.DateTimeField(db_index=True)),
                ("payload_sha256", models.CharField(max_length=64)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("complete", "Complete"),
                            ("partial", "Partial"),
                            ("empty", "No usable observations"),
                        ],
                        max_length=20,
                    ),
                ),
                ("sensor_reading_count", models.PositiveIntegerField(default=0)),
                ("actuator_state_count", models.PositiveIntegerField(default=0)),
                ("setpoint_count", models.PositiveIntegerField(default=0)),
                ("missing_fields", models.JSONField(blank=True, default=list)),
                ("invalid_fields", models.JSONField(blank=True, default=list)),
                ("ingested_at", models.DateTimeField(auto_now_add=True)),
                (
                    "source",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="records",
                        to="sensor_ingest.ingestionsourcestate",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="ingestionrecord",
            constraint=models.UniqueConstraint(
                fields=("source", "source_entry_id"),
                name="unique_ingestion_source_entry",
            ),
        ),
        migrations.AddIndex(
            model_name="ingestionrecord",
            index=models.Index(
                fields=["source", "source_measured_at"],
                name="ingest_source_time_idx",
            ),
        ),
    ]
