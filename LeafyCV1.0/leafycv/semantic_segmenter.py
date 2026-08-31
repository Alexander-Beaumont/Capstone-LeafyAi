from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import torch


DEFAULT_MODEL_PATH = (
    Path(__file__).resolve().parents[1]
    / "models"
    / "leafy_canopy_effnet_b0_final.pth"
)


class SemanticCanopySegmenter:
    """U-Net canopy segmenter using the bundled EfficientNet-B0 checkpoint.

    The model is loaded once and reused for all images. Training preprocessing is
    reproduced exactly: BGR -> RGB, resize to 512x512, float32 / 255.0.
    """

    def __init__(
        self,
        model_path: str | Path | None = None,
        *,
        device: str | None = None,
    ) -> None:
        configured_path = model_path or os.getenv("LEAFY_CV_MODEL_PATH") or DEFAULT_MODEL_PATH
        self.model_path = Path(configured_path)
        self.device = self._resolve_device(device or os.getenv("LEAFY_CV_DEVICE", "auto"))
        self.model: Any | None = None
        self.input_size = 512
        self.threshold = 0.5
        self.encoder = "efficientnet-b0"
        self.architecture = "unet"
        self.preprocessing: dict[str, Any] = {
            "color_space": "RGB",
            "pixel_scaling": "divide_by_255",
            "normalization": None,
        }

    @staticmethod
    def _resolve_device(value: str) -> torch.device:
        value = str(value).strip().lower()
        if value in ("", "auto"):
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if value == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("LEAFY_CV_DEVICE=cuda was requested, but CUDA is not available.")
        return torch.device(value)

    @staticmethod
    def _load_checkpoint(path: Path) -> Any:
        # PyTorch 2.6+ supports weights_only. The packaged checkpoint is sanitized
        # so it can be loaded safely with weights_only=True.
        try:
            return torch.load(path, map_location="cpu", weights_only=True)
        except TypeError:
            # Compatibility with older PyTorch versions that do not expose the
            # weights_only argument.
            return torch.load(path, map_location="cpu")

    def ensure_loaded(self) -> None:
        if self.model is not None:
            return
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"LeafyCV semantic model not found: {self.model_path}. "
                "Set LEAFY_CV_MODEL_PATH or place the checkpoint in models/."
            )

        checkpoint = self._load_checkpoint(self.model_path)
        if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
            state_dict = checkpoint["model_state_dict"]
            self.architecture = str(checkpoint.get("architecture", "unet")).lower()
            self.encoder = str(checkpoint.get("encoder", "efficientnet-b0"))
            self.input_size = int(checkpoint.get("input_size", 512))
            self.threshold = float(checkpoint.get("threshold", 0.5))
            self.preprocessing = dict(checkpoint.get("preprocessing") or self.preprocessing)
            in_channels = int(checkpoint.get("in_channels", 3))
            classes = int(checkpoint.get("classes", 1))
        else:
            # Plain state_dict compatibility.
            state_dict = checkpoint
            in_channels = 3
            classes = 1

        if self.architecture != "unet":
            raise ValueError(f"Unsupported checkpoint architecture: {self.architecture}")
        if self.preprocessing.get("color_space", "RGB").upper() != "RGB":
            raise ValueError("This LeafyCV build expects RGB training preprocessing.")
        if self.preprocessing.get("normalization") not in (None, "none"):
            raise ValueError("This LeafyCV build expects no mean/std normalization.")

        try:
            import segmentation_models_pytorch as smp
        except ImportError as exc:
            raise RuntimeError(
                "segmentation-models-pytorch is required. Run: pip install -r requirements.txt"
            ) from exc

        model = smp.Unet(
            encoder_name=self.encoder,
            encoder_weights=None,
            in_channels=in_channels,
            classes=classes,
        )
        model.load_state_dict(state_dict, strict=True)
        model.to(self.device)
        model.eval()
        self.model = model

    def segment(self, image_bgr: np.ndarray) -> dict[str, np.ndarray | float | str]:
        """Return probability map and OpenCV-friendly binary canopy mask.

        mask uses 0 for background and 255 for canopy. The returned mask and
        probability map have the same width/height as the supplied image.
        """
        if image_bgr is None or image_bgr.size == 0:
            raise ValueError("Cannot segment an empty image.")

        self.ensure_loaded()
        assert self.model is not None

        original_h, original_w = image_bgr.shape[:2]
        rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(
            rgb,
            (self.input_size, self.input_size),
            interpolation=cv2.INTER_LINEAR,
        )
        array = resized.astype(np.float32) / 255.0
        array = np.transpose(array, (2, 0, 1))
        tensor = torch.from_numpy(array).unsqueeze(0).to(self.device)

        with torch.inference_mode():
            logits = self.model(tensor)
            probability_small = torch.sigmoid(logits)[0, 0].detach().cpu().numpy()

        mask_small = (probability_small >= self.threshold).astype(np.uint8) * 255
        mask = cv2.resize(
            mask_small,
            (original_w, original_h),
            interpolation=cv2.INTER_NEAREST,
        )
        probability = cv2.resize(
            probability_small.astype(np.float32),
            (original_w, original_h),
            interpolation=cv2.INTER_LINEAR,
        )

        return {
            "mask": mask,
            "probability": probability,
            "threshold": float(self.threshold),
            "device": str(self.device),
        }


_DEFAULT_SEGMENTER: SemanticCanopySegmenter | None = None


def get_default_segmenter() -> SemanticCanopySegmenter:
    global _DEFAULT_SEGMENTER
    if _DEFAULT_SEGMENTER is None:
        _DEFAULT_SEGMENTER = SemanticCanopySegmenter()
    return _DEFAULT_SEGMENTER
