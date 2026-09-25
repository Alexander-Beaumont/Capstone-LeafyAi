import logging
from dataclasses import dataclass

import requests
from django.conf import settings
from django.utils import timezone
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from sensor_ingest.exceptions import (
    IngestionConfigurationError,
    SourcePayloadError,
    SourceTransportError,
)
from sensor_ingest.services.mapper import (
    REQUIRED_SENSOR_SLUGS,
    SENSOR_DEFINITIONS_BY_SLUG,
    normalize_payloads,
)
from telemetry.models import FarmDevice, Sensor, SensorReading


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CollectionResult:
    stored_count: int
    missing_sensors: tuple[str, ...]
    invalid_sensors: tuple[str, ...]
    collected_at: object

    def as_dict(self):
        return {
            "stored_count": self.stored_count,
            "missing_sensors": list(self.missing_sensors),
            "invalid_sensors": list(self.invalid_sensors),
            "collected_at": self.collected_at,
        }


class SensorCollector:
    """Collect one device using a database configuration or legacy settings."""

    def __init__(self, *, configuration=None, device=None, session=None):
        self.configuration = configuration
        self.water_quality_url = str(
            configuration.water_quality_url if configuration else settings.LEAFY_WATER_QUALITY_URL
        ).strip()
        self.ambient_sensor_url = str(
            configuration.ambient_sensor_url if configuration else settings.LEAFY_AMBIENT_SENSOR_URL
        ).strip()
        self.device_slug = str(
            configuration.device.slug if configuration else settings.SENSOR_INGEST_DEVICE_SLUG
        ).strip()
        self.session = session or self._build_session()
        self._device = device or (configuration.device if configuration else None)
        self._sensors = None

    def _build_session(self):
        session = requests.Session()
        retry = Retry(
            total=settings.SENSOR_INGEST_HTTP_RETRY_TOTAL,
            connect=settings.SENSOR_INGEST_HTTP_RETRY_TOTAL,
            read=settings.SENSOR_INGEST_HTTP_RETRY_TOTAL,
            status=settings.SENSOR_INGEST_HTTP_RETRY_TOTAL,
            backoff_factor=settings.SENSOR_INGEST_HTTP_RETRY_BACKOFF,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET"]),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

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

    @property
    def sensors(self):
        if self._sensors is None:
            self._sensors = {
                sensor.slug: sensor
                for sensor in Sensor.objects.filter(
                    device=self.device,
                    slug__in=REQUIRED_SENSOR_SLUGS,
                    enabled=True,
                )
            }
        return self._sensors

    def validate_configuration(self):
        missing = []
        if not self.water_quality_url:
            missing.append("water_quality_url")
        if not self.ambient_sensor_url:
            missing.append("ambient_sensor_url")
        if not self.device_slug:
            missing.append("device")
        if missing:
            raise IngestionConfigurationError(
                "Missing sensor-ingest settings: " + ", ".join(missing)
            )
        missing_sensors = sorted(set(REQUIRED_SENSOR_SLUGS) - set(self.sensors))
        if missing_sensors:
            raise IngestionConfigurationError(
                "Required sensors are not configured or enabled for device "
                f"'{self.device.slug}': {', '.join(missing_sensors)}. "
                "Run `python manage.py seed_sensors`."
            )
        return True

    def _get_json(self, url, source_name):
        try:
            response = self.session.get(
                url,
                timeout=settings.SENSOR_INGEST_HTTP_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise SourceTransportError(
                f"{source_name} request failed: {exc.__class__.__name__}"
            ) from exc
        try:
            payload = response.json()
        except ValueError as exc:
            raise SourcePayloadError(f"{source_name} returned invalid JSON.") from exc
        if not isinstance(payload, dict):
            raise SourcePayloadError(f"{source_name} returned an invalid payload.")
        return payload

    def collect(self, *, store=True):
        self.validate_configuration()
        water_payload = self._get_json(self.water_quality_url, "Water-quality sensor")
        ambient_payload = self._get_json(self.ambient_sensor_url, "Ambient/level sensor")
        normalized = normalize_payloads(water_payload, ambient_payload)
        measured_at = timezone.now()
        readings = [
            SensorReading(
                sensor=self.sensors[slug],
                value=value.value,
                measured_at=measured_at,
                source="local_http",
                source_channel_id=SENSOR_DEFINITIONS_BY_SLUG[slug].source,
                source_entry_id=None,
                quality_status=value.quality_status,
                quality_notes=value.quality_notes,
            )
            for slug, value in normalized.sensor_values.items()
        ]
        if store:
            SensorReading.objects.bulk_create(readings)
        logger.info(
            "Local sensor cycle stored %s reading(s); missing=%s invalid=%s",
            len(readings) if store else 0,
            list(normalized.missing_sensors),
            list(normalized.invalid_sensors),
        )
        return CollectionResult(
            stored_count=len(readings) if store else 0,
            missing_sensors=normalized.missing_sensors,
            invalid_sensors=normalized.invalid_sensors,
            collected_at=measured_at,
        )

    def collect_latest(self):
        """Compatibility entry point returning the number of stored readings."""
        return self.collect(store=True).stored_count
