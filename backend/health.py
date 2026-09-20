from django.conf import settings
from django.utils import timezone


def source_health_dict(source, *, now=None):
    now = now or timezone.now()

    collector_status = "never_started"
    collector_age_seconds = None
    if source.last_attempt_at is not None:
        collector_age_seconds = max(
            0, round((now - source.last_attempt_at).total_seconds())
        )
        heartbeat_limit = max(int(settings.SENSOR_INGEST_POLL_SECONDS) * 3, 60)
        collector_status = (
            "active" if collector_age_seconds <= heartbeat_limit else "stale"
        )

    connection_status = "unknown"
    if source.last_http_success_at is not None:
        connection_status = "online"
        if source.last_attempt_at and source.last_attempt_at > source.last_http_success_at:
            connection_status = "degraded"
    elif source.last_attempt_at is not None:
        connection_status = "offline"

    feed_status = "unknown"
    age_seconds = None
    if source.last_source_measured_at is not None:
        age_seconds = max(
            0,
            round((now - source.last_source_measured_at).total_seconds()),
        )
        stale_seconds = int(settings.SENSOR_INGEST_FEED_STALE_SECONDS)
        feed_status = "fresh" if age_seconds <= stale_seconds else "stale"

    return {
        "key": source.key,
        "provider": source.provider,
        "external_source_id": source.external_source_id,
        "collector_status": collector_status,
        "collector_heartbeat_age_seconds": collector_age_seconds,
        "connection_status": connection_status,
        "feed_status": feed_status,
        "last_attempt_at": (
            source.last_attempt_at.isoformat() if source.last_attempt_at else None
        ),
        "last_http_success_at": (
            source.last_http_success_at.isoformat()
            if source.last_http_success_at
            else None
        ),
        "last_new_entry_at": (
            source.last_new_entry_at.isoformat() if source.last_new_entry_at else None
        ),
        "last_source_entry_id": source.last_source_entry_id,
        "last_measurement_at": (
            source.last_source_measured_at.isoformat()
            if source.last_source_measured_at
            else None
        ),
        "measurement_age_seconds": age_seconds,
        "consecutive_failures": source.consecutive_failures,
        "last_error_code": source.last_error_code or None,
        "last_error_message": source.last_error_message or None,
    }
