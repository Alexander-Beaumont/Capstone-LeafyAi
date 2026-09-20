"""Direct Lab sensor collector using the team's Django ingestion boundary.

Seven physical readings are supported.  Each valid reading is persisted
independently, so a failed ambient sensor does not discard valid water-quality
or water-level data and vice versa.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.utils import timezone

from sensor_ingest.clients.lab_http import LabHTTPClient
from sensor_ingest.exceptions import IngestionConfigurationError, SensorIngestError
from sensor_ingest.models import IngestionSourceState
from sensor_ingest.services.mapper import LAB_SENSOR_DEFINITIONS
from telemetry.models import FarmDevice, ObservationQuality, Sensor, SensorReading


class LabSensorCollector:
    WATER_SOURCE_KEY = "lab-water-quality"
    AMBIENT_SOURCE_KEY = "lab-ambient"

    def __init__(self, *, client=None):
        self.water_url = str(settings.LEAFY_WATER_QUALITY_URL or "").strip()
        self.ambient_url = str(settings.LEAFY_AMBIENT_SENSOR_URL or "").strip()
        self.device_slug = str(settings.SENSOR_INGEST_DEVICE_SLUG or "").strip()
        self._client = client
        self._device = None
        self._sensors = None

    @property
    def client(self):
        if self._client is None:
            self._client = LabHTTPClient(
                timeout_seconds=settings.LEAFY_SENSOR_HTTP_TIMEOUT,
                retry_total=settings.SENSOR_INGEST_HTTP_RETRY_TOTAL,
                backoff_factor=settings.SENSOR_INGEST_HTTP_RETRY_BACKOFF,
            )
        return self._client

    @property
    def device(self):
        if self._device is not None:
            return self._device

        if self.device_slug:
            try:
                self._device = FarmDevice.objects.get(slug=self.device_slug)
            except FarmDevice.DoesNotExist as exc:
                raise IngestionConfigurationError(
                    f"FarmDevice slug '{self.device_slug}' does not exist."
                ) from exc
            return self._device

        devices = list(FarmDevice.objects.all().order_by("id")[:2])
        if len(devices) == 1:
            self._device = devices[0]
            return self._device
        if not devices:
            raise IngestionConfigurationError(
                "No FarmDevice exists for Lab sensor ingestion."
            )
        raise IngestionConfigurationError(
            "Multiple FarmDevice rows exist; set SENSOR_INGEST_DEVICE_SLUG."
        )

    def validate_configuration(self):
        if not (self.water_url or self.ambient_url):
            raise IngestionConfigurationError(
                "Set LEAFY_WATER_QUALITY_URL and/or LEAFY_AMBIENT_SENSOR_URL."
            )
        self._ensure_sensors()
        return True

    def _ensure_sensors(self):
        if self._sensors is not None:
            return self._sensors

        sensors = {}
        for definition in LAB_SENSOR_DEFINITIONS:
            defaults = {
                "sensor_type": definition.sensor_type,
                "unit": definition.unit,
                "enabled": True,
                "expected_interval_seconds": int(settings.SENSOR_INGEST_EXPECTED_INTERVAL_SECONDS),
                "stale_after_seconds": int(settings.SENSOR_INGEST_SENSOR_STALE_SECONDS),
            }
            sensor = Sensor.objects.filter(
                device=self.device, slug=definition.slug
            ).first()
            if sensor is None:
                # Reuse a pre-existing row with the same canonical type when
                # possible instead of creating a duplicate Farm Overview card.
                sensor = Sensor.objects.filter(
                    device=self.device, sensor_type=definition.sensor_type
                ).order_by("id").first()
            if sensor is None:
                sensor = Sensor.objects.create(
                    device=self.device,
                    slug=definition.slug,
                    **defaults,
                )
            changed = False
            if sensor.slug != definition.slug:
                sensor.slug = definition.slug
                changed = True
            if sensor.sensor_type != definition.sensor_type:
                sensor.sensor_type = definition.sensor_type
                changed = True
            if sensor.unit != definition.unit:
                sensor.unit = definition.unit
                changed = True
            if not sensor.enabled:
                sensor.enabled = True
                changed = True
            if changed:
                sensor.save()
            sensors[definition.slug] = sensor
        self._sensors = sensors
        return sensors

    def _source_state(self, key: str, url: str):
        source, _ = IngestionSourceState.objects.get_or_create(
            key=key,
            defaults={
                "provider": "lab_http",
                "external_source_id": str(url)[:100],
            },
        )
        # Keep the same key reusable for the same provider; refresh the URL in
        # case a Lab IP changes between sessions.
        changed = False
        if source.provider != "lab_http":
            raise IngestionConfigurationError(
                f"Ingestion source key '{key}' is already bound to provider "
                f"'{source.provider}'."
            )
        if source.external_source_id != str(url)[:100]:
            source.external_source_id = str(url)[:100]
            changed = True
        if changed:
            source.save(update_fields=["external_source_id", "updated_at"])
        return source

    @staticmethod
    def _number(payload: dict, key: str):
        raw = payload.get(key)
        if raw is None or raw == "":
            return None
        try:
            value = Decimal(str(raw))
        except (InvalidOperation, TypeError, ValueError):
            return None
        return value if value.is_finite() else None

    def _fetch(self, *, key: str, url: str, label: str):
        if not url:
            return {}, None
        source = self._source_state(key, url)
        now = timezone.now()
        source.last_attempt_at = now
        source.save(update_fields=["last_attempt_at", "updated_at"])
        try:
            payload = self.client.get_json(url, label=label)
        except SensorIngestError as exc:
            source.consecutive_failures += 1
            source.last_error_code = getattr(exc, "code", exc.__class__.__name__)
            source.last_error_message = str(exc)[:1000]
            source.save(
                update_fields=[
                    "consecutive_failures",
                    "last_error_code",
                    "last_error_message",
                    "updated_at",
                ]
            )
            return {}, source

        source.last_http_success_at = now
        source.consecutive_failures = 0
        source.last_error_code = ""
        source.last_error_message = ""
        source.save(
            update_fields=[
                "last_http_success_at",
                "consecutive_failures",
                "last_error_code",
                "last_error_message",
                "updated_at",
            ]
        )
        return payload, source

    def _persist(self, values: dict[str, tuple[Decimal, str]], measured_at) -> int:
        sensors = self._ensure_sensors()
        rows = []
        for slug, (value, source_channel) in values.items():
            sensor = sensors.get(slug)
            if sensor is None or value is None:
                continue
            rows.append(
                SensorReading(
                    sensor=sensor,
                    value=value,
                    measured_at=measured_at,
                    source="lab_http",
                    source_channel_id=source_channel,
                    source_entry_id=None,
                    quality_status=ObservationQuality.VALID,
                    quality_notes="",
                )
            )
        if rows:
            SensorReading.objects.bulk_create(rows)
        return len(rows)

    def collect_latest(self) -> int:
        self.validate_configuration()
        now = timezone.now()
        values: dict[str, tuple[Decimal, str]] = {}

        water, water_state = self._fetch(
            key=self.WATER_SOURCE_KEY,
            url=self.water_url,
            label="water-quality",
        )
        if water:
            if bool(water.get("ph_valid")):
                value = self._number(water, "ph")
                if value is not None:
                    values["water_ph"] = (value, self.WATER_SOURCE_KEY)
            if bool(water.get("ec_valid")):
                value = self._number(water, "ec")
                if value is not None:
                    values["electrical_conductivity"] = (value, self.WATER_SOURCE_KEY)
            if bool(water.get("water_temperature_valid")):
                value = self._number(water, "water_temperature_c")
                if value is not None:
                    values["water_temperature"] = (value, self.WATER_SOURCE_KEY)

        ambient, ambient_state = self._fetch(
            key=self.AMBIENT_SOURCE_KEY,
            url=self.ambient_url,
            label="ambient/level",
        )
        if ambient:
            if bool(ambient.get("ambient_valid")):
                for payload_key, slug in (
                    ("ambient_temperature_c", "ambient_temperature"),
                    ("humidity_percent", "relative_humidity"),
                    ("dew_point_c", "dew_point"),
                ):
                    value = self._number(ambient, payload_key)
                    if value is not None:
                        values[slug] = (value, self.AMBIENT_SOURCE_KEY)
            if bool(ambient.get("water_level_valid")):
                value = self._number(ambient, "water_level")
                if value is not None:
                    values["reservoir_water_level"] = (value, self.AMBIENT_SOURCE_KEY)

        count = self._persist(values, now)

        for source, source_key in (
            (water_state, self.WATER_SOURCE_KEY),
            (ambient_state, self.AMBIENT_SOURCE_KEY),
        ):
            if source is None:
                continue
            if any(channel == source_key for _, channel in values.values()):
                source.last_new_entry_at = now
                source.last_source_measured_at = now
                source.save(
                    update_fields=[
                        "last_new_entry_at",
                        "last_source_measured_at",
                        "updated_at",
                    ]
                )

        return count
