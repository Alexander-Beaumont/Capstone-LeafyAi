from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.utils import timezone

from farm_state.thresholds import FRESH_THRESHOLD_SECONDS
from telemetry.models import (
    ActuatorStateObservation,
    BatchPlacement,
    Camera,
    CameraImage,
    FarmDevice,
    FarmLevel,
    GrowingArea,
    NutrientTank,
    ObservationQuality,
    Sensor,
    SensorReading,
    SetpointObservation,
)


def _status_for(as_of, now=None, threshold_seconds=None):
    """Classify freshness independently from measurement quality."""

    if as_of is None:
        return "missing"
    now = now or timezone.now()
    threshold = (
        FRESH_THRESHOLD_SECONDS
        if threshold_seconds is None
        else int(threshold_seconds)
    )
    age = (now - as_of).total_seconds()
    return "fresh" if age <= threshold else "stale"


def latest_reading(sensor):
    return (
        SensorReading.objects.filter(sensor=sensor)
        .order_by("-measured_at", "-id")
        .first()
    )


def sensor_trend(sensor, now):
    """Return compact deterministic trend statistics for recent readings.

    Suspect observations are retained in history but excluded from trend
    summaries so a physically implausible value cannot dominate an automated
    trend calculation. Unverified values remain usable for sources that do not
    provide a definitive hardware validity signal.
    """

    window_minutes = int(settings.FARM_STATE_SENSOR_TREND_WINDOW_MINUTES)
    window_start = now - timedelta(minutes=window_minutes)
    readings = list(
        SensorReading.objects.filter(
            sensor=sensor,
            measured_at__gte=window_start,
        )
        .exclude(quality_status=ObservationQuality.SUSPECT)
        .order_by("measured_at", "id")
        .values_list("value", "measured_at")
    )

    if not readings:
        return {
            "window_minutes": window_minutes,
            "sample_count": 0,
            "mean": None,
            "minimum": None,
            "maximum": None,
            "change": None,
            "direction": "insufficient_data",
        }

    values = [value for value, _ in readings]
    mean = sum(values, Decimal("0")) / Decimal(len(values))
    minimum = min(values)
    maximum = max(values)

    change = None
    direction = "insufficient_data"
    if len(values) >= 2:
        change = values[-1] - values[0]
        # Treat sub-0.5% changes as effectively stable while keeping a small
        # absolute floor for values close to zero.
        tolerance = max(abs(values[0]) * Decimal("0.005"), Decimal("0.001"))
        if change > tolerance:
            direction = "rising"
        elif change < -tolerance:
            direction = "falling"
        else:
            direction = "stable"

    return {
        "window_minutes": window_minutes,
        "sample_count": len(values),
        "mean": float(mean),
        "minimum": float(minimum),
        "maximum": float(maximum),
        "change": float(change) if change is not None else None,
        "direction": direction,
    }


def latest_image(camera):
    return (
        CameraImage.objects.filter(camera=camera)
        .order_by("-captured_at", "-id")
        .first()
    )


def current_batch(area):
    placement = (
        BatchPlacement.objects.filter(growing_area=area, end_date__isnull=True)
        .select_related("plant_batch")
        .order_by("-start_date")
        .first()
    )
    return placement.plant_batch if placement else None


def tank_info(device):
    return NutrientTank.objects.filter(device=device).first()


def _camera_state(camera, now):
    image = latest_image(camera)
    if image is None:
        return {
            "camera_id": camera.id,
            "name": camera.name,
            "status": "missing",
            "image_id": None,
            "as_of": None,
            "age_seconds": None,
        }

    as_of = image.captured_at
    return {
        "camera_id": camera.id,
        "name": camera.name,
        "as_of": as_of.isoformat(),
        "age_seconds": max(0, round((now - as_of).total_seconds())),
        "status": _status_for(as_of, now),
        "image_id": image.id,
        "vlm_ready": image.vlm_ready,
        "quality_status": image.quality_status,
        "quality_flags": image.quality_flags,
        "quality_message": image.quality_message,
    }


def _sensor_state(sensor, now):
    reading = latest_reading(sensor)
    stale_threshold = sensor.stale_after_seconds or FRESH_THRESHOLD_SECONDS

    if reading is None:
        return {
            "sensor_id": sensor.id,
            "sensor_slug": sensor.slug,
            "sensor_type": sensor.sensor_type,
            "unit": sensor.unit,
            "enabled": sensor.enabled,
            "expected_interval_seconds": sensor.expected_interval_seconds,
            "stale_after_seconds": stale_threshold,
            "value": None,
            "as_of": None,
            "measured_at": None,
            "received_at": None,
            "age_seconds": None,
            "status": "missing",
            "quality_status": None,
            "quality_notes": "",
            "source": None,
            "source_entry_id": None,
            "trend": sensor_trend(sensor, now),
        }

    measured_at = reading.measured_at
    return {
        "sensor_id": sensor.id,
        "sensor_slug": sensor.slug,
        "sensor_type": sensor.sensor_type,
        "unit": sensor.unit,
        "enabled": sensor.enabled,
        "expected_interval_seconds": sensor.expected_interval_seconds,
        "stale_after_seconds": stale_threshold,
        "value": float(reading.value),
        # as_of is retained for backwards compatibility with AI/safety code.
        "as_of": measured_at.isoformat(),
        "measured_at": measured_at.isoformat(),
        "received_at": reading.received_at.isoformat(),
        "age_seconds": max(0, round((now - measured_at).total_seconds())),
        "status": _status_for(measured_at, now, stale_threshold),
        "quality_status": reading.quality_status,
        "quality_notes": reading.quality_notes,
        "source": reading.source,
        "source_channel_id": reading.source_channel_id or None,
        "source_entry_id": reading.source_entry_id,
        "sensor_reading_id": reading.id,
        "trend": sensor_trend(sensor, now),
    }


def _area_state(area, now):
    batch = current_batch(area)
    return {
        "growing_area_id": area.id,
        "name": area.name,
        "slot_count": area.slot_count,
        "current_batch": (
            {
                "batch_id": batch.id,
                "plant_type": batch.plant_type,
                "planting_date": batch.planting_date.isoformat(),
                "growth_stage": batch.growth_stage,
            }
            if batch
            else None
        ),
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
            for area in GrowingArea.objects.filter(farm_level=level).order_by("id")
        ],
    }


def _latest_actuator_states(device, now):
    latest_by_slug = {}
    observations = ActuatorStateObservation.objects.filter(device=device).order_by(
        "actuator_slug", "-measured_at", "-id"
    )
    for observation in observations:
        if observation.actuator_slug in latest_by_slug:
            continue
        latest_by_slug[observation.actuator_slug] = {
            "actuator_slug": observation.actuator_slug,
            "state": observation.state,
            "measured_at": observation.measured_at.isoformat(),
            "received_at": observation.received_at.isoformat(),
            "age_seconds": max(
                0, round((now - observation.measured_at).total_seconds())
            ),
            "source": observation.source,
            "source_entry_id": observation.source_entry_id,
            "quality_status": observation.quality_status,
            "quality_notes": observation.quality_notes,
        }
    return list(latest_by_slug.values())


def _latest_setpoints(device, now):
    latest_by_slug = {}
    observations = SetpointObservation.objects.filter(device=device).order_by(
        "setpoint_slug", "-measured_at", "-id"
    )
    for observation in observations:
        if observation.setpoint_slug in latest_by_slug:
            continue
        latest_by_slug[observation.setpoint_slug] = {
            "setpoint_slug": observation.setpoint_slug,
            "value": float(observation.value),
            "unit": observation.unit,
            "measured_at": observation.measured_at.isoformat(),
            "received_at": observation.received_at.isoformat(),
            "age_seconds": max(
                0, round((now - observation.measured_at).total_seconds())
            ),
            "source": observation.source,
            "source_entry_id": observation.source_entry_id,
            "quality_status": observation.quality_status,
            "quality_notes": observation.quality_notes,
        }
    return list(latest_by_slug.values())


def _device_state(device, now):
    tank = tank_info(device)
    return {
        "device_id": device.id,
        "device_slug": device.slug,
        "name": device.name,
        "sensors": [
            _sensor_state(sensor, now)
            for sensor in Sensor.objects.filter(device=device).order_by("id")
        ],
        "actuator_states": _latest_actuator_states(device, now),
        "setpoints": _latest_setpoints(device, now),
        "nutrient_tank": (
            {
                "capacity_l": float(tank.capacity_l),
                "current_level_l": (
                    float(tank.current_level_l)
                    if tank.current_level_l is not None
                    else None
                ),
                "level_percent": (
                    round(
                        float(tank.current_level_l)
                        / float(tank.capacity_l)
                        * 100,
                        1,
                    )
                    if tank.capacity_l and tank.current_level_l is not None
                    else None
                ),
                "as_of": tank.updated_at.isoformat(),
                "age_seconds": max(
                    0, round((now - tank.updated_at).total_seconds())
                ),
                "status": _status_for(tank.updated_at, now),
            }
            if tank
            else None
        ),
        "levels": [
            _level_state(level, now)
            for level in FarmLevel.objects.filter(device=device).order_by(
                "level_number"
            )
        ],
    }


def build_farm_state(farm):
    """Assemble the complete current farm-state document for a Farm."""

    now = timezone.now()
    return {
        "farm_id": farm.id,
        "generated_at": now.isoformat(),
        "devices": [
            _device_state(device, now)
            for device in FarmDevice.objects.filter(farm=farm).order_by("id")
        ],
    }
