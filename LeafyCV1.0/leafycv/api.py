from __future__ import annotations

import json
from contextlib import ExitStack
from pathlib import Path
from typing import Any

import requests

from . import MODEL_VERSION


def build_backend_payload(result: dict[str, Any]) -> dict[str, Any]:
    """Build the Computer Vision payload expected by the Leafy AI backend."""
    plants: list[dict[str, Any]] = []
    for item in result["plants"]:
        plants.append(
            {
                "slot_id": item["slot_id"],
                "canopy_coverage": round(float(item["canopy_coverage"]), 4),
                "width_px": round(float(item["width_px"]), 4),
                "height_px": round(float(item["height_px"]), 4),
                "width_cm": None if item["width_cm"] is None else round(float(item["width_cm"]), 4),
                "height_cm": None if item["height_cm"] is None else round(float(item["height_cm"]), 4),
                "green_percentage": None if item["green_percentage"] is None else round(float(item["green_percentage"]), 4),
                "yellow_percentage": None if item["yellow_percentage"] is None else round(float(item["yellow_percentage"]), 4),
                "crowding_percentage": round(float(item["crowding_percentage"]), 4),
                "growth_change": round(float(item["growth_change"]), 4),
                "visible": bool(item["visible"]),
                "measurement_valid": bool(item["measurement_valid"]),
            }
        )

    payload = {
        "model_version": MODEL_VERSION,
        "camera_name": result["camera_name"],
        "captured_at": result["captured_at"],
        "lighting_mode": result["lighting_mode"],
        "size_calibrated": bool(result["size_calibrated"]),
        "colour_measurement_valid": bool(result["colour_measurement_valid"]),
        "analysis": {
            "total_canopy_coverage": round(float(result["analysis"]["total_canopy_coverage"]), 4),
            "visible_plant_count": int(result["analysis"]["visible_plant_count"]),
            "measurement_valid": bool(result["analysis"]["measurement_valid"]),
            "processing_time_ms": int(result["analysis"]["processing_time_ms"]),
        },
        "plants": plants,
    }
    camera_id = result.get("camera_id")
    if camera_id:
        payload["camera_id"] = str(camera_id)
    return payload


class CVApiClient:
    """Posts scheduled CV samples to the Leafy AI Django backend."""

    def __init__(self, url: str = "", api_key: str = "", timeout: float = 5.0):
        self.url = (url or "").strip()
        self.api_key = (api_key or "").strip()
        self.timeout = max(0.5, float(timeout))

    @property
    def enabled(self) -> bool:
        return bool(self.url)

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": MODEL_VERSION,
            "X-Leafy-CV-Version": MODEL_VERSION,
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def send_sample(
        self,
        *,
        payload: dict[str, Any],
        raw_path: Path,
        annotated_path: Path,
        mask_path: Path,
        image_mode: str = "raw",
    ) -> bool:
        if not self.enabled:
            return False
        try:
            if image_mode == "none":
                response = requests.post(
                    self.url,
                    json=payload,
                    headers=self._headers(),
                    timeout=self.timeout,
                )
            else:
                with ExitStack() as stack:
                    files: dict[str, tuple] = {}
                    raw_file = stack.enter_context(raw_path.open("rb"))
                    files["raw_image"] = (raw_path.name, raw_file, "image/jpeg")
                    if image_mode == "all":
                        annotated_file = stack.enter_context(annotated_path.open("rb"))
                        mask_file = stack.enter_context(mask_path.open("rb"))
                        files["annotated_image"] = (annotated_path.name, annotated_file, "image/jpeg")
                        files["mask_image"] = (mask_path.name, mask_file, "image/png")
                    response = requests.post(
                        self.url,
                        data={"metadata": json.dumps(payload)},
                        files=files,
                        headers=self._headers(),
                        timeout=self.timeout,
                    )
            if 200 <= response.status_code < 300:
                print(f"Backend API accepted the sample (HTTP {response.status_code}).")
                return True
            print(f"Backend API warning: HTTP {response.status_code}: {response.text[:400]}")
            return False
        except Exception as exc:
            print(f"Backend API warning: send failed: {exc}. Local CV outputs remain saved.")
            return False


class BackendConfigClient:
    """Reads the current camera configuration from the Django backend.

    This is the bridge that allows React -> Django/database changes to become
    visible to LeafyCV without maintaining a second manual configuration.
    """

    def __init__(self, base_url: str, camera_id: str, api_key: str = "", timeout: float = 5.0):
        self.base_url = (base_url or "").strip().rstrip("/")
        self.camera_id = str(camera_id or "").strip()
        self.api_key = (api_key or "").strip()
        self.timeout = max(0.5, float(timeout))
        if not self.base_url:
            raise ValueError("A backend base URL is required for backend-driven configuration.")
        if not self.camera_id:
            raise ValueError("A camera ID is required for backend-driven configuration.")

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": MODEL_VERSION,
            "X-Leafy-CV-Version": MODEL_VERSION,
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _get_json(self, path: str) -> Any:
        url = f"{self.base_url}{path}"
        response = requests.get(url, headers=self._headers(), timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    @property
    def ingest_url(self) -> str:
        return f"{self.base_url}/api/cv/ingest/"

    def fetch_camera_config(self) -> dict[str, Any]:
        from .config import config_from_backend

        camera_payload = self._get_json(f"/api/cv/cameras/{self.camera_id}/config/")
        slot_payload = self._get_json(f"/api/cv/cameras/{self.camera_id}/slot-positions/")
        return config_from_backend(camera_payload, slot_payload)
