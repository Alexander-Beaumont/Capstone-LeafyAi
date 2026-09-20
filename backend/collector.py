import logging

from django.conf import settings
from django.utils import timezone

from sensor_ingest.clients.thingspeak import ThingSpeakClient
from sensor_ingest.exceptions import (
    IngestionConfigurationError,
    SensorIngestError,
    SourcePayloadError,
)
from sensor_ingest.models import IngestionSourceState
from sensor_ingest.services.ingestion import ingest_snapshot
from sensor_ingest.services.mapper import REQUIRED_SENSOR_SLUGS, normalize_entry
from sensor_ingest.services.parser import parse_entry
from telemetry.models import FarmDevice, Sensor


logger = logging.getLogger(__name__)


class SensorCollector:
    """Coordinates ThingSpeak transport, normalization and persistence."""

    def __init__(self, *, client=None):
        self.channel_id = str(settings.THINGSPEAK_CHANNEL_ID or "").strip()
        self.read_api_key = str(settings.THINGSPEAK_READ_API_KEY or "").strip()
        self.device_slug = str(settings.SENSOR_INGEST_DEVICE_SLUG or "").strip()
        self.source_key = str(settings.SENSOR_INGEST_SOURCE_KEY or "").strip()

        self._client = client
        self._device = None
        self._source_state = None

    @property
    def client(self):
        if self._client is None:
            self._client = ThingSpeakClient(
                channel_id=self.channel_id,
                read_api_key=self.read_api_key,
                connect_timeout_seconds=settings.SENSOR_INGEST_CONNECT_TIMEOUT_SECONDS,
                read_timeout_seconds=settings.SENSOR_INGEST_READ_TIMEOUT_SECONDS,
                retry_total=settings.SENSOR_INGEST_HTTP_RETRY_TOTAL,
                backoff_factor=settings.SENSOR_INGEST_HTTP_RETRY_BACKOFF,
            )
        return self._client

    @property
    def source_state(self):
        if self._source_state is None:
            self._source_state, _ = IngestionSourceState.objects.get_or_create(
                key=self.source_key,
                defaults={
                    "provider": "thingspeak",
                    "external_source_id": self.channel_id,
                },
            )
            if self._source_state.provider != "thingspeak":
                raise IngestionConfigurationError(
                    f"Ingestion source key '{self.source_key}' is already bound to "
                    f"provider '{self._source_state.provider}'. Use a new source key."
                )
            if self._source_state.external_source_id != self.channel_id:
                raise IngestionConfigurationError(
                    f"Ingestion source key '{self.source_key}' is already bound to "
                    f"external source '{self._source_state.external_source_id}', not "
                    f"channel '{self.channel_id}'. Use a new source key for a new channel."
                )
        return self._source_state

    @property
    def device(self):
        if self._device is None:
            try:
                self._device = FarmDevice.objects.get(slug=self.device_slug)
            except FarmDevice.DoesNotExist as exc:
                raise IngestionConfigurationError(
                    f"FarmDevice slug '{self.device_slug}' does not exist."
                ) from exc
        return self._device

    def validate_configuration(self):
        missing_settings = []
        if not self.channel_id:
            missing_settings.append("THINGSPEAK_CHANNEL_ID")
        if not self.read_api_key:
            missing_settings.append("THINGSPEAK_READ_API_KEY")
        if not self.device_slug:
            missing_settings.append("SENSOR_INGEST_DEVICE_SLUG")
        if not self.source_key:
            missing_settings.append("SENSOR_INGEST_SOURCE_KEY")
        if missing_settings:
            raise IngestionConfigurationError(
                "Missing sensor-ingest settings: " + ", ".join(missing_settings)
            )

        device = self.device
        configured = set(
            Sensor.objects.filter(device=device, slug__in=REQUIRED_SENSOR_SLUGS)
            .values_list("slug", flat=True)
        )
        missing_sensors = sorted(set(REQUIRED_SENSOR_SLUGS) - configured)
        if missing_sensors:
            raise IngestionConfigurationError(
                "Required sensors are not configured for device "
                f"'{device.slug}': {', '.join(missing_sensors)}. "
                "Run `python manage.py seed_sensors`."
            )

        # Materialize the source row only after all static settings are valid.
        self.source_state
        return True

    def _mark_attempt(self):
        source = self.source_state
        source.last_attempt_at = timezone.now()
        source.save(update_fields=["last_attempt_at", "updated_at"])

    def _mark_http_success(self):
        source = self.source_state
        source.last_http_success_at = timezone.now()
        source.save(update_fields=["last_http_success_at", "updated_at"])

    def _mark_success(self, entry, *, created):
        source = self.source_state
        now = timezone.now()
        source.consecutive_failures = 0
        source.last_error_code = ""
        source.last_error_message = ""

        current_time = source.last_source_measured_at
        if current_time is None or entry.measured_at >= current_time:
            source.last_source_entry_id = entry.entry_id
            source.last_source_measured_at = entry.measured_at
        if created:
            source.last_new_entry_at = now

        source.save(
            update_fields=[
                "consecutive_failures",
                "last_error_code",
                "last_error_message",
                "last_source_entry_id",
                "last_source_measured_at",
                "last_new_entry_at",
                "updated_at",
            ]
        )

    def _mark_failure(self, exc):
        source = self.source_state
        source.consecutive_failures += 1
        source.last_error_code = getattr(exc, "code", "unexpected_error")
        source.last_error_message = str(exc)[:2000]
        source.save(
            update_fields=[
                "consecutive_failures",
                "last_error_code",
                "last_error_message",
                "updated_at",
            ]
        )

    def _process_payload(self, payload):
        entry = parse_entry(payload)
        snapshot = normalize_entry(entry)
        result = ingest_snapshot(
            source_state=self.source_state,
            device=self.device,
            snapshot=snapshot,
        )
        self._mark_success(entry, created=result.created)
        return entry, result

    def collect_latest(self):
        self.validate_configuration()
        self._mark_attempt()
        try:
            payload = self.client.get_latest()
            self._mark_http_success()
            entry, result = self._process_payload(payload)
        except Exception as exc:
            self._mark_failure(exc)
            if isinstance(exc, SensorIngestError):
                raise
            raise

        logger.info(
            "ThingSpeak latest entry processed: entry_id=%s status=%s created=%s "
            "sensor_readings=%s actuator_states=%s setpoints=%s missing=%s invalid=%s",
            entry.entry_id,
            result.status,
            result.created,
            result.sensor_reading_count,
            result.actuator_state_count,
            result.setpoint_count,
            list(result.missing_fields),
            list(result.invalid_fields),
        )
        return result

    def reconcile(self, *, results=100):
        results = int(results)
        if not 1 <= results <= 8000:
            raise IngestionConfigurationError(
                "ThingSpeak reconciliation results must be between 1 and 8000."
            )
        self.validate_configuration()
        self._mark_attempt()
        try:
            payloads = self.client.get_recent(results=results)
            self._mark_http_success()
        except Exception as exc:
            self._mark_failure(exc)
            raise

        parsed = []
        parse_errors = []
        for payload in payloads:
            try:
                parsed.append(parse_entry(payload))
            except SourcePayloadError as exc:
                parse_errors.append(str(exc))
                logger.warning("Skipping malformed ThingSpeak history entry: %s", exc)

        parsed.sort(key=lambda item: (item.measured_at, item.entry_id))

        created = 0
        duplicates = 0
        partial = 0
        empty = 0
        latest_entry = None

        try:
            for entry in parsed:
                snapshot = normalize_entry(entry)
                result = ingest_snapshot(
                    source_state=self.source_state,
                    device=self.device,
                    snapshot=snapshot,
                )
                latest_entry = entry
                if result.created:
                    created += 1
                else:
                    duplicates += 1
                if result.status == "partial":
                    partial += 1
                elif result.status == "empty":
                    empty += 1
                self._mark_success(entry, created=result.created)
        except Exception as exc:
            self._mark_failure(exc)
            raise

        if parsed and latest_entry is not None:
            # _mark_success above already keeps the source cursor at the newest
            # source timestamp.  This branch simply guarantees stale prior
            # failure state is cleared even when every history row duplicated.
            self._mark_success(latest_entry, created=created > 0)
        elif parse_errors:
            exc = SourcePayloadError(
                "All ThingSpeak history entries were malformed."
            )
            self._mark_failure(exc)
            raise exc

        summary = {
            "retrieved": len(payloads),
            "parsed": len(parsed),
            "created": created,
            "duplicates": duplicates,
            "partial": partial,
            "empty": empty,
            "parse_errors": len(parse_errors),
        }
        logger.info("ThingSpeak reconciliation complete: %s", summary)
        return summary
