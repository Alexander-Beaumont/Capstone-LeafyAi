from pathlib import Path

import torch


def test_bundled_checkpoint_metadata():
    path = Path(__file__).resolve().parents[1] / "models" / "leafy_canopy_effnet_b0_final.pth"
    checkpoint = torch.load(path, map_location="cpu", weights_only=True)
    assert checkpoint["architecture"] == "unet"
    assert checkpoint["encoder"] == "efficientnet-b0"
    assert checkpoint["input_size"] == 512
    assert checkpoint["in_channels"] == 3
    assert checkpoint["classes"] == 1
    assert checkpoint["threshold"] == 0.5
    assert checkpoint["preprocessing"]["color_space"] == "RGB"
    assert checkpoint["preprocessing"]["pixel_scaling"] == "divide_by_255"
    assert checkpoint["preprocessing"]["normalization"] is None
    assert len(checkpoint["model_state_dict"]) > 0
