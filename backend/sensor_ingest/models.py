from django.db import models


class IngestionSourceState(models.Model):
    """Operational state of one external telemetry source.

    Connection health and feed freshness are intentionally separate.  A source
    can return HTTP 200 while its newest measurement is old.
    """

    key = models.SlugField(max_length=80, primary_key=True)
    provider = models.CharField(max_length=50)
    external_source_id = models.CharField(max_length=100)

    last_attempt_at = models.DateTimeField(null=True, blank=True)
    last_http_success_at = models.DateTimeField(null=True, blank=True)
    last_new_entry_at = models.DateTimeField(null=True, blank=True)
    last_source_entry_id = models.PositiveBigIntegerField(null=True, blank=True)
    last_source_measured_at = models.DateTimeField(null=True, blank=True)

    consecutive_failures = models.PositiveIntegerField(default=0)
    last_error_code = models.CharField(max_length=100, blank=True, default="")
    last_error_message = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.provider}:{self.external_source_id}"


class IngestionRecord(models.Model):
    """Audit record proving how an external source entry was processed."""

    class Status(models.TextChoices):
        COMPLETE = "complete", "Complete"
        PARTIAL = "partial", "Partial"
        EMPTY = "empty", "No usable observations"

    source = models.ForeignKey(
        IngestionSourceState,
        on_delete=models.PROTECT,
        related_name="records",
    )
    source_entry_id = models.PositiveBigIntegerField()
    source_measured_at = models.DateTimeField(db_index=True)
    payload_sha256 = models.CharField(max_length=64)

    status = models.CharField(max_length=20, choices=Status.choices)
    sensor_reading_count = models.PositiveIntegerField(default=0)
    actuator_state_count = models.PositiveIntegerField(default=0)
    setpoint_count = models.PositiveIntegerField(default=0)
    missing_fields = models.JSONField(default=list, blank=True)
    invalid_fields = models.JSONField(default=list, blank=True)

    ingested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source", "source_entry_id"],
                name="unique_ingestion_source_entry",
            )
        ]
        indexes = [
            models.Index(
                fields=["source", "source_measured_at"],
                name="ingest_source_time_idx",
            )
        ]

    def __str__(self):
        return f"{self.source_id} entry {self.source_entry_id} ({self.status})"
