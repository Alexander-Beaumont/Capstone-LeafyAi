from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from sensor_ingest.models import SensorIngestConfiguration
from sensor_ingest.services.collector import SensorCollector
from core.operation_locks import operation_lock


def record_result(configuration, error=None):
    now = timezone.now()
    configuration.last_attempt_at = now
    fields = ["last_attempt_at", "updated_at"]
    if error is None:
        configuration.last_success_at = now
        configuration.last_error = ""
        configuration.consecutive_failures = 0
        fields += ["last_success_at", "last_error", "consecutive_failures"]
    else:
        configuration.last_error = str(error)
        configuration.consecutive_failures += 1
        fields += ["last_error", "consecutive_failures"]
    configuration.save(update_fields=fields)


def perform_collection(configuration, *, store=True):
    try:
        result = SensorCollector(configuration=configuration).collect(store=store)
    except Exception as exc:
        record_result(configuration, exc)
        raise
    record_result(configuration)
    return result


def configuration_is_due(configuration, now=None):
    if not configuration.enabled:
        return False
    if configuration.last_attempt_at is None:
        return True
    delay = configuration.poll_interval_seconds
    if configuration.consecutive_failures:
        backoff = int(settings.SENSOR_INGEST_FAILURE_BACKOFF_BASE_SECONDS) * (
            2 ** (configuration.consecutive_failures - 1)
        )
        delay = max(
            delay,
            min(int(settings.SENSOR_INGEST_FAILURE_BACKOFF_MAX_SECONDS), backoff),
        )
    return (now or timezone.now()) >= configuration.last_attempt_at + timedelta(seconds=delay)


def collect_due_configurations(now=None):
    now = now or timezone.now()
    completed = 0
    configurations = SensorIngestConfiguration.objects.filter(
        enabled=True
    ).select_related("device").order_by("device_id")
    for configuration in configurations:
        if not configuration_is_due(configuration, now):
            continue
        lock = operation_lock("sensor-collect", configuration.device_id)
        if not lock.acquire(blocking=False):
            continue
        try:
            try:
                perform_collection(configuration)
                completed += 1
            except Exception:
                # Status is persisted by perform_collection; one failed
                # controller must not prevent another one from collecting.
                continue
        finally:
            lock.release()
    return completed
