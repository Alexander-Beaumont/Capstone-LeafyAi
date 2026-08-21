from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cv2


def save_debug_outputs(output_dir: Path, stem: str, result: dict[str, Any]) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    annotated_path = output_dir / f"{stem}_annotated.jpg"
    mask_path = output_dir / f"{stem}_mask.png"
    result_path = output_dir / f"{stem}_result.json"

    cv2.imwrite(str(annotated_path), result["annotated"])
    cv2.imwrite(str(mask_path), result["mask"])
    serializable = {
        "analysis": result["analysis"],
        "quality": result["quality"],
        "growth_area_pixels": result["growth_area_pixels"],
    }
    result_path.write_text(json.dumps(serializable, indent=2), encoding="utf-8")
    return {"annotated": annotated_path, "mask": mask_path, "result": result_path}
