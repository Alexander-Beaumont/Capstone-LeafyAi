from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np


def save_debug_outputs(
    output_dir: Path,
    stem: str,
    result: dict[str, Any],
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    annotated_path = output_dir / f"{stem}_annotated.jpg"
    mask_path = output_dir / f"{stem}_mask.png"
    probability_path = output_dir / f"{stem}_probability.png"
    result_path = output_dir / f"{stem}_result.json"

    cv2.imwrite(str(annotated_path), result["annotated"])
    cv2.imwrite(str(mask_path), result["mask"])

    paths = {"annotated": annotated_path, "mask": mask_path, "result": result_path}
    probability = result.get("probability")
    if isinstance(probability, np.ndarray):
        probability_u8 = np.clip(probability * 255.0, 0, 255).astype(np.uint8)
        cv2.imwrite(str(probability_path), probability_u8)
        paths["probability"] = probability_path

    serializable = {
        "analysis": result["analysis"],
        "quality": result["quality"],
        "growth_area_pixels": result["growth_area_pixels"],
        "model": result.get("model", {}),
    }
    result_path.write_text(json.dumps(serializable, indent=2), encoding="utf-8")
    return paths
