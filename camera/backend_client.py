"""HTTP client for the standalone Camera -> Django Backend boundary."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import requests

from . import SERVICE_VERSION


class BackendClient:
    """Read Camera config and upload official JPEGs through documented APIs."""

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
        """Build common request headers and include JWT when configured."""
        headers = {
            "Accept": "application/json",
            "User-Agent": SERVICE_VERSION,
            "X-Leafy-Camera-Version": SERVICE_VERSION,
        }
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _refresh_access_token(self) -> bool:
        """Refresh the JWT once when the backend returns HTTP 401."""
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
        """Send one authenticated request, retrying once after JWT refresh."""
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
        """Return every Backend Camera record, including all DRF pages.

        The Backend may return either a plain JSON list or the standard DRF
        pagination object with ``results`` and ``next``. Multi-camera services
        must not silently ignore Cameras that happen to be on page 2+.
        """
        cameras: list[dict[str, Any]] = []
        path_or_url: str | None = "/api/cameras/"
        pages = 0

        while path_or_url:
            pages += 1
            if pages > 100:
                raise RuntimeError("Camera pagination exceeded 100 pages; aborting possible loop.")

            response = self.request("GET", path_or_url)
            response.raise_for_status()
            payload = response.json()

            if isinstance(payload, list):
                cameras.extend(item for item in payload if isinstance(item, dict))
                break

            if isinstance(payload, dict) and isinstance(payload.get("results"), list):
                cameras.extend(item for item in payload["results"] if isinstance(item, dict))
                next_url = payload.get("next")
                path_or_url = str(next_url) if next_url else None
                continue

            raise ValueError("GET /api/cameras/ must return a list or paginated results.")

        return cameras

    def get_camera(self, camera_id: Any) -> dict[str, Any]:
        """Return configuration for one backend Camera ID."""
        response = self.request("GET", f"/api/cameras/{camera_id}/")
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("Camera endpoint must return a JSON object.")
        return payload

    def get_latest_image(self, camera_id: Any) -> dict[str, Any] | None:
        """Read the newest official CameraImage for scheduling decisions."""
        response = self.request("GET", f"/api/cv/cameras/{camera_id}/latest-image/")
        if response.status_code == 404:
            return None
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else None

    def upload_official_image(
        self,
        camera_id: Any,
        jpeg_bytes: bytes,
        *,
        captured_at: datetime,
    ) -> dict[str, Any]:
        """Upload one already-encoded official JPEG to the existing endpoint."""
        if not jpeg_bytes:
            raise ValueError("Official JPEG bytes are empty.")

        files = {
            "image": ("official.jpg", jpeg_bytes, "image/jpeg"),
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
