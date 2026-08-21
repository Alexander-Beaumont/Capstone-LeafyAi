from __future__ import annotations

from datetime import datetime
from typing import Any

import cv2
import requests

from . import SERVICE_VERSION


class BackendClient:
    """HTTP boundary between the standalone Camera service and Django."""

    def __init__(
        self,
        base_url: str,
        *,
        access_token: str = "",
        refresh_token: str = "",
        timeout: float = 15.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token.strip()
        self.refresh_token = refresh_token.strip()
        self.timeout = max(1.0, float(timeout))
        if not self.base_url:
            raise ValueError("Backend base URL is required.")

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": SERVICE_VERSION,
            "X-Leafy-Camera-Version": SERVICE_VERSION,
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

    def request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        url = path if path.startswith(("http://", "https://")) else f"{self.base_url}{path}"
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

    def get_cameras(self) -> list[dict[str, Any]]:
        response = self.request("GET", "/api/cameras/")
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        # Supports DRF pagination if enabled later.
        if isinstance(payload, dict) and isinstance(payload.get("results"), list):
            return [item for item in payload["results"] if isinstance(item, dict)]
        raise ValueError("GET /api/cameras/ must return a list or DRF paginated results.")

    def get_camera(self, camera_id: Any) -> dict[str, Any]:
        response = self.request("GET", f"/api/cameras/{camera_id}/")
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Camera endpoint must return a JSON object.")
        return payload

    def get_latest_image(self, camera_id: Any) -> dict[str, Any] | None:
        response = self.request("GET", f"/api/cv/cameras/{camera_id}/latest-image/")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else None

    def upload_official_image(
        self,
        camera_id: Any,
        frame,
        *,
        captured_at: datetime,
        jpeg_quality: int = 92,
    ) -> dict[str, Any]:
        quality = max(50, min(100, int(jpeg_quality)))
        ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        if not ok:
            raise ValueError("Could not encode camera frame as JPEG.")

        files = {
            "image": ("official.jpg", encoded.tobytes(), "image/jpeg"),
        }
        data = {
            "captured_at": captured_at.isoformat(),
        }
        response = self.request(
            "POST",
            f"/api/cameras/{camera_id}/official-image/",
            files=files,
            data=data,
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        payload = response.json() if response.content else {}
        return payload if isinstance(payload, dict) else {}
