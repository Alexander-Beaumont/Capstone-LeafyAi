import cv2
import numpy as np

from camera_capture.quality import assess_image_quality


def test_quality_gate_rejects_tiny_blurry_image():
    image = np.full((100, 100, 3), 120, dtype=np.uint8)
    result = assess_image_quality(image)
    assert result["quality_status"] == "FAIL"
    assert result["vlm_ready"] is False
    assert "LOW_RESOLUTION" in result["quality_flags"]


def test_quality_gate_passes_large_textured_image():
    base = np.indices((480, 640)).sum(axis=0).astype(np.uint8)
    image = np.stack([base, np.roll(base, 17, 1), np.roll(base, 29, 0)], axis=2)
    result = assess_image_quality(image)
    assert result["quality_status"] == "PASS"
    assert result["vlm_ready"] is True


def test_magenta_cast_is_warning_but_remains_vlm_ready():
    # Textured magenta scene: strong red+blue cast, but still enough focus/contrast
    # for VLM use. Magenta alone must never block the image.
    yy, xx = np.indices((480, 640))
    pattern = ((xx // 16 + yy // 16) % 2) * 100
    image = np.empty((480, 640, 3), dtype=np.uint8)
    image[:, :, 0] = np.clip(145 + pattern, 0, 255).astype(np.uint8)  # blue
    image[:, :, 1] = np.clip(45 + pattern // 4, 0, 255).astype(np.uint8)  # green
    image[:, :, 2] = np.clip(150 + pattern, 0, 255).astype(np.uint8)  # red
    result = assess_image_quality(image)
    assert result["quality_status"] == "WARN"
    assert result["vlm_ready"] is True
    assert "MAGENTA_CAST" in result["quality_flags"]


def test_quality_gate_rejects_monochrome_or_ir_like_frame():
    # Sharp, correctly exposed IR/night frame: luminance passes, colour must fail.
    yy, xx = np.indices((480, 640))
    gray = ((xx + yy) % 160 + 40).astype(np.uint8)
    image = np.stack([gray, gray, gray], axis=2)
    result = assess_image_quality(image)
    assert result["quality_status"] == "FAIL"
    assert result["vlm_ready"] is False
    assert "MONOCHROME_OR_IR" in result["quality_flags"]
    assert result["quality_metrics"]["mean_saturation"] < 1.0


def test_quality_gate_rejects_strongly_blurred_full_size_frame():
    rng = np.random.default_rng(7)
    image = rng.integers(0, 256, size=(480, 640, 3), dtype=np.uint8)
    image = cv2.GaussianBlur(image, (15, 15), 0)
    result = assess_image_quality(image)
    assert result["quality_status"] == "FAIL"
    assert result["vlm_ready"] is False
    assert "BLURRY" in result["quality_flags"]
