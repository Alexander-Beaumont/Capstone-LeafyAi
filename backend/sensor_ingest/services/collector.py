import logging

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


class SensorCollector:
    """Collect physical sensor readings directly from LeafyAI local devices."""

    def __init__(self, *, session=None):
        self.water_quality_url = str(
            settings.LEAFY_WATER_QUALITY_URL or ""
        ).strip()

        self.ambient_sensor_url = str(
            settings.LEAFY_AMBIENT_SENSOR_URL or ""
        ).strip()

        self.device_slug = str(
            settings.SENSOR_INGEST_DEVICE_SLUG or ""
        ).strip()

        self.session = session or self._build_session()

        self._device = None
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
                self._device = FarmDevice.objects.get(
                    slug=self.device_slug
                )
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
        missing_settings = []

        if not self.water_quality_url:
            missing_settings.append(
                "LEAFY_WATER_QUALITY_URL"
            )

        if not self.ambient_sensor_url:
            missing_settings.append(
                "LEAFY_AMBIENT_SENSOR_URL"
            )

        if not self.device_slug:
            missing_settings.append(
                "SENSOR_INGEST_DEVICE_SLUG"
            )

        if missing_settings:
            raise IngestionConfigurationError(
                "Missing sensor-ingest settings: "
                + ", ".join(missing_settings)
            )

        configured = set(self.sensors)

        missing_sensors = sorted(
            set(REQUIRED_SENSOR_SLUGS) - configured
        )

        if missing_sensors:
            raise IngestionConfigurationError(
                "Required sensors are not configured or enabled "
                f"for device '{self.device.slug}': "
                + ", ".join(missing_sensors)
                + ". Run `python manage.py seed_sensors`."
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
                f"{source_name} request failed: "
                f"{exc.__class__.__name__}"
            ) from exc

        try:
            payload = response.json()

        except ValueError as exc:
            raise SourcePayloadError(
                f"{source_name} returned invalid JSON."
            ) from exc

        if not isinstance(payload, dict):
            raise SourcePayloadError(
                f"{source_name} returned an invalid payload."
            )

        return payload

    def collect_latest(self):
        self.validate_configuration()

        water_payload = self._get_json(
            self.water_quality_url,
            "Water-quality sensor",
        )

        ambient_payload = self._get_json(
            self.ambient_sensor_url,
            "Ambient/level sensor",
        )

        normalized = normalize_payloads(
            water_payload,
            ambient_payload,
        )

        measured_at = timezone.now()

        readings = []

        for slug, normalized_value in normalized.sensor_values.items():
            sensor = self.sensors[slug]

            readings.append(
                SensorReading(
                    sensor=sensor,
                    value=normalized_value.value,
                    measured_at=measured_at,
                    source="local_http",
                    source_channel_id=SENSOR_DEFINITIONS_BY_SLUG[slug].source,
                    source_entry_id=None,
                    quality_status=normalized_value.quality_status,
                    quality_notes=normalized_value.quality_notes,
                )
            )

        SensorReading.objects.bulk_create(readings)

        logger.info(
            "Local sensor cycle stored %s reading(s); "
            "missing=%s invalid=%s",
            len(readings),
            list(normalized.missing_sensors),
            list(normalized.invalid_sensors),
        )

        return len(readings)