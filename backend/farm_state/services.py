from django.utils import timezone

from telemetry.models import (
    FarmDevice, FarmLevel, GrowingArea, Camera,
    Sensor, SensorReading, NutrientTank,
    BatchPlacement, PlantBatch,
)
from cv.models import ImageAnalysis
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

def latest_analysis(camera):
    return (
        ImageAnalysis.objects
        .filter(image__camera=camera)
        .select_related("image")
        .order_by("-image__captured_at", "-id")
        .first()
    )

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

def _camera_state(camera, now):
    analysis = latest_analysis(camera)
    if analysis is None:
        return {"camera_id": camera.id, "name": camera.name, "status": "missing", "analysis": None}

    as_of = analysis.image.captured_at
    return {
        "camera_id": camera.id,
        "name": camera.name,
        "measurement_valid": analysis.measurement_valid,
        "total_canopy_coverage": float(analysis.total_canopy_coverage) if analysis.total_canopy_coverage is not None else None,
        "growth_change": float(analysis.growth_change) if analysis.growth_change is not None else None,
        "crowding_percentage": float(analysis.crowding_percentage) if analysis.crowding_percentage is not None else None,
        "green_percentage": float(analysis.green_percentage) if analysis.green_percentage is not None else None,
        "yellow_percentage": float(analysis.yellow_percentage) if analysis.yellow_percentage is not None else None,
        "as_of": as_of.isoformat(),
        "age_seconds": round((now - as_of).total_seconds()),
        "status": _status_for(as_of, now),
        "analysis_id": analysis.id,
        "image_id": analysis.image_id,
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
    batch = current_batch(area)
    return {
        "growing_area_id": area.id,
        "name": area.name,
        "slot_count": area.slot_count,
        "current_batch": {
            "batch_id": batch.id,
            "plant_type": batch.plant_type,
            "planting_date": batch.planting_date.isoformat(),
            "growth_stage": batch.growth_stage,
        } if batch else None,
    }

def _level_state(level, now):
    return {
        "level_number": level.level_number,
        "cameras": [
            _camera_state(camera, now)
            for camera in Camera.objects.filter(farm_level=level).order_by("id")
        ],
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
