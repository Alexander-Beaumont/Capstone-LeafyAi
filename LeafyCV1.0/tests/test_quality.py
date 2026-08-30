import numpy as np

from leafycv.quality import assess_image_quality


def textured_neutral_image(height=480, width=640):
    rng = np.random.default_rng(7)
    base = rng.integers(70, 190, size=(height, width, 3), dtype=np.uint8)
    return base


def test_quality_pass_for_textured_neutral_image():
    result = assess_image_quality(textured_neutral_image())
    assert result["quality_status"] == "PASS"
    assert result["measurement_valid"] is True
    assert result["vlm_ready"] is True
    assert result["quality_flags"] == []


def test_magenta_cast_blocks_vlm():
    image = np.zeros((480, 640, 3), dtype=np.uint8)
    # BGR: strong blue + red with weak green -> magenta cast.
    image[:, :] = [210, 35, 210]
    # Add texture so the failure is specifically not dependent on blur alone.
    image[::2, ::2] = [240, 50, 240]
    result = assess_image_quality(image)
    assert "MAGENTA_CAST" in result["quality_flags"]
    assert result["vlm_ready"] is False
    assert result["quality_status"] == "FAIL"


def test_invalid_roi_blocks_vlm():
    result = assess_image_quality(
        textured_neutral_image(),
        roi_configured=True,
        roi_valid=False,
    )
    assert "INVALID_ROI" in result["quality_flags"]
    assert result["vlm_ready"] is False
