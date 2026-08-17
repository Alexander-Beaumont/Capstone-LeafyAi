from django.utils import timezone

from telemetry.models import (
    FarmDevice, FarmLevel, GrowingArea, Slot,
    Sensor, SensorReading, NutrientTank,
    BatchPlacement, PlantBatch,
)
from cv.models import PlantVisionMeasurement, ImageAnalysis
from farm_state.thresholds import FRESH_THRESHOLD_SECONDS

def _status_for(as_of, now=None):
    """Classify a value's freshness.

    Returns "missing" (no row at all), "fresh", or "stale".
    as_of is the datetime the value was recorded (or None).
    """
    if as_of is None:
        return "missing"
    now = now or timezone.now()
    age = (now - as_of).total_seconds()
    return "fresh" if age <= FRESH_THRESHOLD_SECONDS else "stale"

def latest_reading(sensor):
    """Newest SensorReading for a sensor, or None."""
    return (
        SensorReading.objects
        .filter(sensor=sensor)
        .order_by("-timestamp")
        .first()
    )

def latest_vision_by_slot(area):
    """{slot_id: latest PlantVisionMeasurement} for every slot in an area.

    One query for all slots, ordered so per-slot ordering is correct,
    then grouped in Python by keeping the first of each slot.
    """
    slot_ids = list(
        Slot.objects
        .filter(growing_area=area)
        .values_list("id", flat=True)
    )
    measurements = (
        PlantVisionMeasurement.objects
        .filter(slot_id__in=slot_ids)
        .select_related("image_analysis", "slot")
        .order_by("slot_id", "-image_analysis__created_at")
    )
    latest = {}
    for m in measurements:
        # setdefault keeps the FIRST (= newest, given the ordering) per slot
        latest.setdefault(m.slot_id, m)
    return latest

def current_batch(area):
    """PlantBatch currently placed in an area, or None.

    "Current" = a BatchPlacement with end_date NULL.
    The schema permits multiple open placements (only the
    (plant_batch, growing_area) pair is unique), so take the
    newest start_date as the display value for now.
    """
    placement = (
        BatchPlacement.objects
        .filter(growing_area=area, end_date__isnull=True)
        .select_related("plant_batch")
        .order_by("-start_date")
        .first()
    )
    return placement.plant_batch if placement else None

def tank_info(device):
    """NutrientTank for a device, or None."""
    return (
        NutrientTank.objects
        .filter(device=device)   # OneToOne, but .filter never raises
        .first()
    )

def _slot_state(slot, measurement, now):
    if measurement is None:
        return {"slot_id": slot.id, "status": "missing"}

    as_of = measurement.image_analysis.created_at
    return {
        "slot_id": slot.id,
        "canopy_coverage": float(measurement.canopy_coverage) if measurement.canopy_coverage is not None else None,
        "growth_stage": measurement.growth_stage,
        "measurement_valid": measurement.measurement_valid,
        "as_of": as_of.isoformat(),
        "age_seconds": round((now - as_of).total_seconds()),
        "status": _status_for(as_of, now),
        "analysis_id": measurement.image_analysis_id,
    }

def _sensor_state(sensor, now):
    reading = latest_reading(sensor)
    if reading is None:
        return {
            "sensor_type": sensor.sensor_type,
            "unit": sensor.unit,
            "value": None,
            "as_of": None,
            "age_seconds": None,
            "status": "missing",
        }
    return {
        "sensor_type": sensor.sensor_type,
        "unit": sensor.unit,
        "value": float(reading.value),
        "as_of": reading.timestamp.isoformat(),
        "age_seconds": round((now - reading.timestamp).total_seconds()),
        "status": _status_for(reading.timestamp, now),
        "sensor_reading_id": reading.id,
    }

def _area_state(area, now):
    latest = latest_vision_by_slot(area)
    batch = current_batch(area)
    return {
        "growing_area_id": area.id,
        "name": area.name,
        "current_batch": {
            "batch_id": batch.id,
            "plant_type": batch.plant_type,
            "planting_date": batch.planting_date.isoformat(),
            "growth_stage": batch.growth_stage,
        } if batch else None,
        "slots": [
            _slot_state(slot, latest.get(slot.id), now)
            for slot in Slot.objects.filter(growing_area=area)
        ],
    }

def _level_state(level, now):
    return {
        "level_number": level.level_number,
        "growing_areas": [
            _area_state(area, now)
            for area in GrowingArea.objects.filter(farm_level=level)
        ],
    }

def _device_state(device, now):
    tank = tank_info(device)
    return {
        "device_id": device.id,
        "name": device.name,
        "sensors": [
            _sensor_state(sensor, now)
            for sensor in Sensor.objects.filter(device=device)
        ],
        "nutrient_tank": {
            "capacity_l": float(tank.capacity_l),
            "current_level_l": (
                float(tank.current_level_l)
                if tank.current_level_l is not None else None
            ),
            "level_percent": (
                round(float(tank.current_level_l) / float(tank.capacity_l) * 100, 1)
                if tank.capacity_l and tank.current_level_l is not None else None
            ),
            # Guard: capacity_l is truthy (nonzero) BEFORE dividing.
            "as_of": tank.updated_at.isoformat(),
            "age_seconds": round((now - tank.updated_at).total_seconds()),
            "status": _status_for(tank.updated_at, now),
        } if tank else None,
        "levels": [
            _level_state(level, now)
            for level in FarmLevel.objects.filter(device=device)
        ],
    }

def build_farm_state(farm):
    """Assemble the complete farm-state document for a Farm."""
    now = timezone.now()
    return {
        "farm_id": farm.id,
        "generated_at": now.isoformat(),
        "devices": [
            _device_state(device, now)
            for device in FarmDevice.objects.filter(farm=farm)
        ],
    }