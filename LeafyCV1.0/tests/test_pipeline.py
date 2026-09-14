import numpy as np

from leafycv.pipeline import analyse_image


class HalfCanopySegmenter:
    def segment(self, image_bgr):
        h, w = image_bgr.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        mask[:, : w // 2] = 255
        probability = mask.astype(np.float32) / 255.0
        return {
            "mask": mask,
            "probability": probability,
            "threshold": 0.5,
            "device": "test",
        }


class FullCanopySegmenter:
    def segment(self, image_bgr):
        h, w = image_bgr.shape[:2]
        mask = np.full((h, w), 255, dtype=np.uint8)
        return {
            "mask": mask,
            "probability": np.ones((h, w), dtype=np.float32),
            "threshold": 0.5,
            "device": "test",
        }


def textured_image(height=480, width=640):
    rng = np.random.default_rng(3)
    return rng.integers(40, 210, size=(height, width, 3), dtype=np.uint8)


def test_pipeline_uses_semantic_mask_for_canopy():
    image = textured_image()
    result = analyse_image(image, segmenter=HalfCanopySegmenter())
    assert result["analysis"]["total_canopy_coverage"] == 50.0
    assert result["mask"].shape == image.shape[:2]
    assert set(np.unique(result["mask"]).tolist()).issubset({0, 255})
    assert result["analysis"]["quality_status"] == "PASS"
    assert result["analysis"]["vlm_ready"] is True
    assert "growth_stage" not in result["analysis"]
    assert "visible_plant_count" not in result["analysis"]


def test_roi_denominator_is_roi_not_full_frame():
    image = textured_image(480, 800)
    cfg = {"roi_points": {"x": 0.5, "y": 0.0, "width": 0.5, "height": 1.0}}
    result = analyse_image(image, camera_config=cfg, segmenter=FullCanopySegmenter())
    assert result["analysis"]["total_canopy_coverage"] == 100.0
    assert np.count_nonzero(result["mask"]) == 480 * 400


def test_growth_change_uses_previous_valid_canopy():
    image = textured_image()
    result = analyse_image(
        image,
        previous_canopy=40.0,
        segmenter=HalfCanopySegmenter(),
    )
    assert result["analysis"]["growth_change"] == 25.0


def test_invalid_roi_marks_result_not_vlm_ready():
    image = textured_image()
    cfg = {"roi_points": {"x": 0.8, "y": 0.2, "width": 0.5, "height": 0.5}}
    result = analyse_image(image, camera_config=cfg, segmenter=HalfCanopySegmenter())
    assert result["analysis"]["measurement_valid"] is False
    assert result["analysis"]["vlm_ready"] is False
    assert "INVALID_ROI" in result["analysis"]["quality_flags"]
    assert result["analysis"]["growth_change"] is None
