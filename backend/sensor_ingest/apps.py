from django.apps import AppConfig


class SensorIngestConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sensor_ingest"

    def ready(self):
        from sensor_ingest import signals  # noqa: F401
