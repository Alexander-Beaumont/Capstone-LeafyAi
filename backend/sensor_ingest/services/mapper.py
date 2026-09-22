from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Dict, Tuple

from telemetry.models import ObservationQuality


@dataclass(frozen=True)
class SensorDefinition:
    slug: str
    sensor_type: str
    unit: str
    source: str
    payload_key: str
    valid_key: str


@dataclass(frozen=True)
class NormalizedValue:
    value: Decimal
    quality_status: str
    quality_notes: str = ""


@dataclass(frozen=True)
class NormalizedBatch:
    sensor_values: Dict[str, NormalizedValue]
    missing_sensors: Tuple[str, ...]
    invalid_sensors: Tuple[str, ...]


# ---------------------------------------------------------------------------
# Physical LeafyAI sensors
#
# water_quality:
#   http://192.168.1.100/readings
#
# ambient:
#   http://192.168.1.111:8080/readings
# ---------------------------------------------------------------------------

SENSOR_DEFINITIONS = (
    SensorDefinition(
        slug="water_ph",
        sensor_type="ph",
        unit="pH",
        source="water_quality",
        payload_key="ph",
        valid_key="ph_valid",
    ),
    SensorDefinition(
        slug="electrical_conductivity",
        sensor_type="ec",
        unit="uS/cm",
        source="water_quality",
        payload_key="ec",
        valid_key="ec_valid",
    ),
    SensorDefinition(
        slug="water_temperature",
        sensor_type="water_temperature",
        unit="°C",
        source="water_quality",
        payload_key="water_temperature_c",
        valid_key="water_temperature_valid",
    ),
    SensorDefinition(
        slug="ambient_temperature",
        sensor_type="ambient_temperature",
        unit="°C",
        source="ambient",
        payload_key="ambient_temperature_c",
        valid_key="ambient_valid",
    ),
    SensorDefinition(
        slug="relative_humidity",
        sensor_type="humidity",
        unit="%",
        source="ambient",
        payload_key="humidity_percent",
        valid_key="ambient_valid",
    ),
    SensorDefinition(
        slug="dew_point",
        sensor_type="dew_point",
        unit="°C",
        source="ambient",
        payload_key="dew_point_c",
        valid_key="ambient_valid",
    ),
    SensorDefinition(
        slug="reservoir_water_level",
        sensor_type="water_level",
        unit="cm",
        source="ambient",
        payload_key="water_level",
        valid_key="water_level_valid",
    ),
)


SENSOR_DEFINITIONS_BY_SLUG = {
    definition.slug: definition
    for definition in SENSOR_DEFINITIONS
}


REQUIRED_SENSOR_SLUGS = tuple(
    definition.slug
    for definition in SENSOR_DEFINITIONS
)


MAX_STORABLE_ABS_VALUE = Decimal("100000000")


def _decimal(raw):
    if raw is None:
        return None

    text = str(raw).strip()

    if not text:
        return None

    try:
        value = Decimal(text)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("not_numeric") from exc

    if not value.is_finite():
        raise ValueError("not_finite")

    if abs(value) >= MAX_STORABLE_ABS_VALUE:
        raise ValueError("out_of_storage_range")

    return value


def _quality_for_sensor(slug, value):
    """
    Only flag physically impossible/basic-domain values here.

    Crop operating ranges belong to the safety/control layer, not ingestion.
    """

    if slug == "water_ph":
        if not (Decimal("0") <= value <= Decimal("14")):
            return (
                ObservationQuality.SUSPECT,
                "pH is outside the physical 0-14 scale.",
            )

    if slug == "relative_humidity":
        if not (Decimal("0") <= value <= Decimal("100")):
            return (
                ObservationQuality.SUSPECT,
                "Relative humidity is outside 0-100%.",
            )

    if slug in (
        "electrical_conductivity",
        "reservoir_water_level",
    ):
        if value < 0:
            return (
                ObservationQuality.SUSPECT,
                "Value cannot normally be negative.",
            )

    return ObservationQuality.VALID, ""


def normalize_payloads(
    water_quality_payload,
    ambient_payload,
):
    """
    Convert the two physical sensor payloads into LeafyAI sensor values.

    water_quality_payload:
        GET http://192.168.1.100/readings

    ambient_payload:
        GET http://192.168.1.111:8080/readings
    """

    payloads = {
        "water_quality": water_quality_payload,
        "ambient": ambient_payload,
    }

    sensor_values = {}
    missing_sensors = []
    invalid_sensors = []

    for definition in SENSOR_DEFINITIONS:
        payload = payloads[definition.source]

        # Hardware explicitly reports whether the measurement is valid.
        if payload.get(definition.valid_key) is not True:
            invalid_sensors.append(definition.slug)
            continue

        raw = payload.get(definition.payload_key)

        if raw is None or not str(raw).strip():
            missing_sensors.append(definition.slug)
            continue

        try:
            value = _decimal(raw)
        except ValueError:
            invalid_sensors.append(definition.slug)
            continue

        quality_status, quality_notes = _quality_for_sensor(
            definition.slug,
            value,
        )

        sensor_values[definition.slug] = NormalizedValue(
            value=value,
            quality_status=quality_status,
            quality_notes=quality_notes,
        )

    return NormalizedBatch(
        sensor_values=sensor_values,
        missing_sensors=tuple(sorted(set(missing_sensors))),
        invalid_sensors=tuple(sorted(set(invalid_sensors))),
    )