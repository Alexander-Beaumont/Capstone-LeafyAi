from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urljoin

import cv2
import numpy as np
import requests

from . import MODEL_VERSION


class BackendClient:
    """HTTP client for the backend-driven LeafyCV final MVP workflow."""

    def __init__(
        self,
        base_url: str,
        *,
        access_token: str = "",
        refresh_token: str = "",
        timeout: float = 10.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token.strip()
        self.refresh_token = refresh_token.strip()
        self.timeout = max(1.0, float(timeout))
        if not self.base_url:
            raise ValueError("Backend base URL is required.")

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": MODEL_VERSION,
            "X-Leafy-CV-Version": MODEL_VERSION,
        }
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _refresh_access_token(self) -> bool:
        if not self.refresh_token:
            return False
        response = requests.post(
            f"{self.base_url}/api/auth/refresh/",
            json={"refresh": self.refresh_token},
            timeout=self.timeout,
        )
        if not (200 <= response.status_code < 300):
            return False
        token = (response.json() or {}).get("access")
        if not token:
            return False
        self.access_token = str(token)
        return True

    def request(self, method: str, path_or_url: str, **kwargs) -> requests.Response:
        url = (
            path_or_url
            if path_or_url.startswith(("http://", "https://"))
            else f"{self.base_url}{path_or_url}"
        )
        kwargs.setdefault("timeout", self.timeout)
        extra_headers = kwargs.pop("headers", {}) or {}
        headers = dict(self._headers())
        headers.update(extra_headers)
        response = requests.request(method, url, headers=headers, **kwargs)
        if response.status_code == 401 and self._refresh_access_token():
            headers = dict(self._headers())
            headers.update(extra_headers)
            response = requests.request(method, url, headers=headers, **kwargs)
        return response

    def get_camera_config(self, camera_id: Any) -> dict[str, Any]:
        response = self.request("GET", f"/api/cameras/{camera_id}/")
        if response.status_code == 404:
            return {}
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else {}

    def get_latest_image(self, camera_id: Any) -> dict[str, Any]:
        response = self.request("GET", f"/api/cv/cameras/{camera_id}/latest-image/")
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Latest-image endpoint must return a JSON object.")
        if "image_id" not in payload:
            raise ValueError("Latest-image response is missing image_id.")
        if not (payload.get("image_url") or payload.get("path")):
            raise ValueError("Latest-image response must include image_url or path.")
        return payload

    def get_latest_analysis(
        self,
        camera_id: Any,
        *,
        valid_only: bool = False,
    ) -> dict[str, Any] | None:
        """Get latest analysis.

        With valid_only=True the backend should return the most recent analysis
        whose measurement_valid=True. This is used only as the growth baseline.
        The normal latest analysis is still used for duplicate-image detection.
        """
        path = f"/api/cv/cameras/{camera_id}/latest-analysis/"
        if valid_only:
            path = f"{path}?{urlencode({'valid': 'true'})}"
        response = self.request("GET", path)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else None

    def load_image(self, image_payload: dict[str, Any]) -> np.ndarray:
        path_value = image_payload.get("path")
        if path_value:
            local_path = Path(str(path_value))
            if local_path.exists():
                image = cv2.imread(str(local_path))
                if image is None:
                    raise ValueError(f"Could not decode local image: {local_path}")
                return image

        image_url = image_payload.get("image_url") or image_payload.get("url") or path_value
        if not image_url:
            raise ValueError("No image URL/path was provided by backend.")
        url = (
            str(image_url)
            if str(image_url).startswith(("http://", "https://"))
            else urljoin(self.base_url + "/", str(image_url).lstrip("/"))
        )
        response = self.request("GET", url, headers={"Accept": "image/*"})
        response.raise_for_status()
        data = np.frombuffer(response.content, dtype=np.uint8)
        image = cv2.imdecode(data, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Backend image response could not be decoded as an image.")
        return image

    def post_analysis(
        self,
        camera_id: Any,
        image_id: Any,
        analysis: dict[str, Any],
    ) -> dict[str, Any]:
        payload = {
            "camera_id": camera_id,
            "image_id": image_id,
            "analysis": analysis,
        }
        response = self.request(
            "POST",
            "/api/cv/ingest/",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        if not response.content:
            return {}
        body = response.json()
        return body if isinstance(body, dict) else {}


def previous_canopy_from_latest(payload: dict[str, Any] | None) -> float | None:
    """Extract canopy from a valid analysis payload.

    The backend valid=true query is the primary guarantee. This check is also
    defensive so an explicitly invalid response is never used as a baseline.
    """
    if not payload:
        return None
    candidates = [
        payload.get("analysis") if isinstance(payload.get("analysis"), dict) else None,
        payload,
    ]
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        if candidate.get("measurement_valid") is False:
            continue
        value = candidate.get("total_canopy_coverage")
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                pass
    return None


def latest_analysis_image_id(payload: dict[str, Any] | None) -> Any:
    if not payload:
        return None
    for key in ("image_id", "camera_image_id"):
        if key in payload:
            return payload[key]
    image = payload.get("image")
    if isinstance(image, dict):
        return image.get("id") or image.get("image_id")
    analysis = payload.get("analysis")
    if isinstance(analysis, dict):
        return analysis.get("image_id") or analysis.get("camera_image_id")
    return None
