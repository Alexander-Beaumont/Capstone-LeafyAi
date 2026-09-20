from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Dict, Optional, Tuple

from telemetry.models import ObservationQuality


@dataclass(frozen=True)
class SensorDefinition:
    field_name: str
    slug: str
    sensor_type: str
    unit: str


@dataclass(frozen=True)
class NormalizedValue:
    value: Decimal
    quality_status: str
    quality_notes: str = ""


@dataclass(frozen=True)
class NormalizedSnapshot:
    entry_id: int
    measured_at: object
    payload_sha256: str
    sensor_values: Dict[str, NormalizedValue]
    irrigation_pump_state: Optional[str]
    target_ec: Optional[NormalizedValue]
    missing_fields: Tuple[str, ...]
    invalid_fields: Tuple[str, ...]


SENSOR_DEFINITIONS = (
    SensorDefinition("field1", "water_ph", "ph", "pH"),
    SensorDefinition("field2", "electrical_conductivity", "ec", "uS/cm"),
    SensorDefinition("field3", "water_temperature", "water_temperature", "°C"),
    SensorDefinition("field4", "ambient_temperature", "ambient_temperature", "°C"),
    SensorDefinition("field5", "relative_humidity", "humidity", "%"),
    SensorDefinition("field6", "reservoir_water_level", "water_level", "cm"),
)

# Direct Lab HTTP adds dew point while preserving the team's existing six
# ThingSpeak sensor definitions and field mapping.
DEW_POINT_SENSOR_DEFINITION = SensorDefinition(
    "lab_dew_point",
    "dew_point",
    "dew_point",
    "°C",
)
LAB_SENSOR_DEFINITIONS = SENSOR_DEFINITIONS + (DEW_POINT_SENSOR_DEFINITION,)
ALL_SENSOR_DEFINITIONS = LAB_SENSOR_DEFINITIONS

SENSOR_DEFINITIONS_BY_FIELD = {
    definition.field_name: definition for definition in SENSOR_DEFINITIONS
}
SENSOR_DEFINITIONS_BY_SLUG = {
    definition.slug: definition for definition in SENSOR_DEFINITIONS
}
REQUIRED_SENSOR_SLUGS = tuple(definition.slug for definition in SENSOR_DEFINITIONS)
LAB_REQUIRED_SENSOR_SLUGS = tuple(
    definition.slug for definition in LAB_SENSOR_DEFINITIONS
)
MAX_STORABLE_ABS_VALUE = Decimal("100000000")  # DECIMAL(12,4) upper magnitude


def _decimal(raw):
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    try:
        value = Decimal(text)
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("not_numeric")
    if not value.is_finite():
        raise ValueError("not_finite")
    if abs(value) >= MAX_STORABLE_ABS_VALUE:
        raise ValueError("out_of_storage_range")
    return value


def _quality_for_sensor(slug, value):
    """Flag only physically impossible/basic-domain values here.

    Crop-safe operating ranges belong to the safety layer and must never cause
    real historical observations to be discarded by ingestion.
    """

    if slug == "water_ph" and not (Decimal("0") <= value <= Decimal("14")):
        return ObservationQuality.SUSPECT, "pH is outside the physical 0-14 scale."
    if slug == "relative_humidity" and not (
        Decimal("0") <= value <= Decimal("100")
    ):
        return ObservationQuality.SUSPECT, "Relative humidity is outside 0-100%."
    if slug in ("electrical_conductivity", "reservoir_water_level") and value < 0:
        return ObservationQuality.SUSPECT, "Value cannot normally be negative."
    return ObservationQuality.UNVERIFIED, ""


def normalize_entry(entry):
    sensor_values = {}
    missing_fields = []
    invalid_fields = []

    for definition in SENSOR_DEFINITIONS:
        raw = entry.fields.get(definition.field_name)
        if raw is None or not str(raw).strip():
            missing_fields.append(definition.field_name)
            continue
        try:
            value = _decimal(raw)
        except ValueError:
            invalid_fields.append(definition.field_name)
            continue

        quality_status, quality_notes = _quality_for_sensor(
            definition.slug, value
        )
        sensor_values[definition.slug] = NormalizedValue(
            value=value,
            quality_status=quality_status,
            quality_notes=quality_notes,
        )

    # field7: observed irrigation-pump relay status, not a sensor.
    irrigation_pump_state = None
    raw_pump = entry.fields.get("field7")
    if raw_pump is None or not str(raw_pump).strip():
        missing_fields.append("field7")
    else:
        try:
            pump_value = _decimal(raw_pump)
        except ValueError:
            invalid_fields.append("field7")
        else:
            if pump_value == Decimal("0"):
                irrigation_pump_state = "off"
            elif pump_value == Decimal("1"):
                irrigation_pump_state = "on"
            else:
                invalid_fields.append("field7")

    # field8: externally reported target EC, not a measured sensor value.
    target_ec = None
    raw_target_ec = entry.fields.get("field8")
    if raw_target_ec is None or not str(raw_target_ec).strip():
        missing_fields.append("field8")
    else:
        try:
            value = _decimal(raw_target_ec)
        except ValueError:
            invalid_fields.append("field8")
        else:
            quality_status = ObservationQuality.UNVERIFIED
            quality_notes = ""
            if value < 0:
                quality_status = ObservationQuality.SUSPECT
                quality_notes = "Target EC cannot normally be negative."
            target_ec = NormalizedValue(
                value=value,
                quality_status=quality_status,
                quality_notes=quality_notes,
            )

    return NormalizedSnapshot(
        entry_id=entry.entry_id,
        measured_at=entry.measured_at,
        payload_sha256=entry.payload_sha256,
        sensor_values=sensor_values,
        irrigation_pump_state=irrigation_pump_state,
        target_ec=target_ec,
        missing_fields=tuple(sorted(set(missing_fields))),
        invalid_fields=tuple(sorted(set(invalid_fields))),
    )
