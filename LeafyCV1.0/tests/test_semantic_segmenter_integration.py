from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("segmentation_models_pytorch")

from leafycv.semantic_segmenter import SemanticCanopySegmenter


def test_real_model_inference_shape_and_binary_mask():
    model_path = Path(__file__).resolve().parents[1] / "models" / "leafy_canopy_effnet_b0_final.pth"
    segmenter = SemanticCanopySegmenter(model_path=model_path, device="cpu")
    image = np.full((96, 160, 3), 100, dtype=np.uint8)
    result = segmenter.segment(image)
    assert result["mask"].shape == (96, 160)
    assert result["probability"].shape == (96, 160)
    assert set(np.unique(result["mask"]).tolist()).issubset({0, 255})
