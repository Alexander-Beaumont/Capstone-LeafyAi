#!/usr/bin/env python3
"""LeafyCV1.0 adapter for the current Django computer_vision models.

Actual backend fields supplied by the project:

ImageAnalysis:
    total_canopy_coverage
    visible_plant_count
    measurement_valid
    processing_time_ms

PlantVisionMeasurement:
    slot_id (IntegerField)
    canopy_coverage
    width_px
    height_px
    width_cm
    height_cm
    green_percentage
    yellow_percentage
    crowding_percentage
    growth_change
    visible
    measurement_valid

The backend creates/links CameraImage and Django-generated IDs. LeafyCV does not
write to the database directly.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

MODEL_VERSION = "LeafyCV1.0"


def add_growth_change(
    metrics: list[dict],
    previous_coverages: dict[int, float],
) -> None:
    """Attach per-slot growth_change in canopy percentage points.

    Definition:
        current smoothed canopy coverage - previous saved sample coverage.

    The first saved sample for a slot is 0.0. A process restart or slot
    re-registration also begins a new local comparison baseline.
    """
    for slot_id, metric in enumerate(metrics, start=1):
        current = float(metric.get("coverage_smooth", 0.0))
        previous = previous_coverages.get(slot_id)
        change = 0.0 if previous is None else current - previous
        metric["growth_change"] = float(change)
        previous_coverages[slot_id] = current


def build_django_payload(
    *,
    camera_name: str,
    captured_at: datetime,
    metrics: list[dict],
    total_canopy: float,
    visible_count: int,
    pixels_per_cm: float | None,
    processing_time_ms: int,
    image_measurement_valid: bool,
) -> dict[str, Any]:
    """Build one payload for the current Django computer_vision models."""
    plants: list[dict[str, Any]] = []

    for slot_id, metric in enumerate(metrics, start=1):
        width_px = float(metric.get("width_smooth", 0.0))
        height_px = float(metric.get("height_smooth", 0.0))

        # Current Django models use non-null FloatField() for cm values.
        # To fit that schema without a migration, 0.0 means "not calibrated".
        # The local CSV also records size_calibrated so this is not confused
        # with a biologically zero-sized plant.
        width_cm = width_px / pixels_per_cm if pixels_per_cm else 0.0
        height_cm = height_px / pixels_per_cm if pixels_per_cm else 0.0

        plant_valid = bool(
            image_measurement_valid and metric.get("visible", False)
        )

        plants.append(
            {
                "slot_id": int(slot_id),
                "canopy_coverage": round(
                    float(metric.get("coverage_smooth", 0.0)), 4
                ),
                "width_px": round(width_px, 4),
                "height_px": round(height_px, 4),
                "width_cm": round(float(width_cm), 4),
                "height_cm": round(float(height_cm), 4),
                "green_percentage": round(
                    float(metric.get("green_percent", 0.0)), 4
                ),
                "yellow_percentage": round(
                    float(metric.get("yellow_percent", 0.0)), 4
                ),
                "crowding_percentage": round(
                    float(metric.get("crowding_percentage", 0.0)), 4
                ),
                "growth_change": round(
                    float(metric.get("growth_change", 0.0)), 4
                ),
                "visible": bool(metric.get("visible", False)),
                "measurement_valid": plant_valid,
            }
        )

    return {
        # These top-level fields help the backend locate/create CameraImage.
        # Exact CameraImage field mapping must be confirmed from telemetry.models.
        "model_version": MODEL_VERSION,
        "camera_name": camera_name,
        "captured_at": captured_at.astimezone().isoformat(timespec="seconds"),
        "size_calibrated": bool(pixels_per_cm),
        "analysis": {
            "total_canopy_coverage": round(float(total_canopy), 4),
            "visible_plant_count": int(visible_count),
            "measurement_valid": bool(image_measurement_valid),
            "processing_time_ms": int(processing_time_ms),
        },
        "plants": plants,
    }
