from datetime import datetime, timezone
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "cv"))

from django_backend_adapter import add_growth_change, build_django_payload


def run():
    previous = {}
    metrics = [
        {
            "coverage_smooth": 40.25,
            "width_smooth": 300.0,
            "height_smooth": 250.0,
            "green_percent": 90.0,
            "yellow_percent": 8.0,
            "crowding_percentage": 50.0,
            "visible": True,
        }
    ]

    add_growth_change(metrics, previous)
    assert metrics[0]["growth_change"] == 0.0

    metrics[0]["coverage_smooth"] = 42.75
    add_growth_change(metrics, previous)
    assert round(metrics[0]["growth_change"], 2) == 2.50

    payload = build_django_payload(
        camera_name="level1_camera1",
        captured_at=datetime(2026, 8, 9, 8, 0, tzinfo=timezone.utc),
        metrics=metrics,
        total_canopy=42.75,
        visible_count=1,
        pixels_per_cm=None,
        processing_time_ms=123,
        image_measurement_valid=True,
    )

    assert payload["model_version"] == "LeafyCV1.0"
    assert payload["analysis"] == {
        "total_canopy_coverage": 42.75,
        "visible_plant_count": 1,
        "measurement_valid": True,
        "processing_time_ms": 123,
    }

    plant = payload["plants"][0]
    expected_keys = {
        "slot_id",
        "canopy_coverage",
        "width_px",
        "height_px",
        "width_cm",
        "height_cm",
        "green_percentage",
        "yellow_percentage",
        "crowding_percentage",
        "growth_change",
        "visible",
        "measurement_valid",
    }
    assert set(plant) == expected_keys
    assert isinstance(plant["slot_id"], int)
    assert plant["slot_id"] == 1
    assert plant["growth_change"] == 2.5
    assert plant["width_cm"] == 0.0
    assert plant["height_cm"] == 0.0
    print("test_django_payload: OK")


if __name__ == "__main__":
    run()
