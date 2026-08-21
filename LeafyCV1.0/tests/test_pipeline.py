import cv2
import numpy as np
from leafycv.pipeline import analyse_image


def test_pipeline_green_area():
    image = np.full((300, 400, 3), 40, dtype=np.uint8)
    cv2.rectangle(image, (80, 60), (320, 260), (30, 180, 40), -1)
    result = analyse_image(image)
    analysis = result["analysis"]
    assert analysis["total_canopy_coverage"] > 20
    assert analysis["green_percentage"] > 50
    assert "growth_stage" not in analysis
    assert "visible_plant_count" not in analysis


def test_roi_reduces_area():
    image = np.full((200, 200, 3), 40, dtype=np.uint8)
    cv2.rectangle(image, (0, 0), (99, 199), (20, 180, 30), -1)
    full = analyse_image(image)["analysis"]["total_canopy_coverage"]
    cfg = {"roi_points": {"x": 0.5, "y": 0.0, "width": 0.5, "height": 1.0}}
    right = analyse_image(image, camera_config=cfg)["analysis"]["total_canopy_coverage"]
    assert full > right
