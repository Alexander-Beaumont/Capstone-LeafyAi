from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import cv2
import numpy as np
import requests

from . import MODEL_VERSION


class BackendClient:
    """HTTP client for Backend -> CameraImage -> LeafyCV -> ImageAnalysis."""

    def __init__(
        self,
        base_url: str,
        *,
        access_token: str = "",
        refresh_token: str = "",
        username: str = "",
        password: str = "",
        timeout: float = 10.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token.strip()
        self.refresh_token = refresh_token.strip()
        self.username = username.strip()
        self.password = password
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


    def _login(self) -> bool:
        """Obtain JWTs from the normal login endpoint for the local MVP runtime."""
        if not self.username or not self.password:
            return False
        response = requests.post(
            f"{self.base_url}/api/auth/login/",
            json={"username": self.username, "password": self.password},
            timeout=self.timeout,
        )
        if not (200 <= response.status_code < 300):
            return False
        payload = response.json() or {}
        access = payload.get("access")
        refresh = payload.get("refresh")
        if not access:
            return False
        self.access_token = str(access)
        if refresh:
            self.refresh_token = str(refresh)
        return True

    def _refresh_access_token(self) -> bool:
        if not self.refresh_token:
            return False
        url = f"{self.base_url}/api/auth/refresh/"
        response = requests.post(
            url,
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

    def request(self, method: str, path_or_url: str, **kwargs: Any) -> requests.Response:
        url = (
            path_or_url
            if path_or_url.startswith(("http://", "https://"))
            else f"{self.base_url}{path_or_url}"
        )
        kwargs.setdefault("timeout", self.timeout)
        extra_headers = dict(kwargs.pop("headers", {}) or {})
        headers = dict(self._headers())
        headers.update(extra_headers)
        if not self.access_token and self.username and self.password:
            self._login()
            headers = dict(self._headers())
            headers.update(extra_headers)

        response = requests.request(method, url, headers=headers, **kwargs)
        if response.status_code == 401 and (self._refresh_access_token() or self._login()):
            headers = dict(self._headers())
            headers.update(extra_headers)
            response = requests.request(method, url, headers=headers, **kwargs)
        return response

    def get_cameras(self) -> list[dict[str, Any]]:
        """Return every Backend Camera record, including all DRF pages.

        LeafyCV uses this only for multi-camera orchestration. Each image still
        keeps its own camera_id/image_id identity.
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

    def get_camera_config(self, camera_id: Any) -> dict[str, Any]:
        response = self.request("GET", f"/api/cameras/{camera_id}/")
        if response.status_code == 404:
            return {}
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else {}

    def get_latest_image(self, camera_id: Any) -> dict[str, Any] | None:
        """Return the newest official CameraImage, or None before first capture."""
        response = self.request("GET", f"/api/cv/cameras/{camera_id}/latest-image/")
        if response.status_code == 404:
            return None
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
        suffix = "?valid=true" if valid_only else ""
        response = self.request(
            "GET",
            f"/api/cv/cameras/{camera_id}/latest-analysis/{suffix}",
        )
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
    if not payload:
        return None
    candidates = [
        payload.get("analysis") if isinstance(payload.get("analysis"), dict) else None,
        payload,
    ]
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        value = candidate.get("total_canopy_coverage")
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                pass
    return None


def analysis_captured_at(payload: dict[str, Any] | None) -> str | None:
    """Return the CameraImage capture timestamp carried by latest-analysis.

    The final Backend contract returns captured_at at the top level. These
    fallbacks keep the client defensive if the timestamp is nested with image
    or analysis identity metadata.
    """
    if not payload:
        return None
    value = payload.get("captured_at")
    if value:
        return str(value)
    image = payload.get("image")
    if isinstance(image, dict) and image.get("captured_at"):
        return str(image["captured_at"])
    analysis = payload.get("analysis")
    if isinstance(analysis, dict) and analysis.get("captured_at"):
        return str(analysis["captured_at"])
    return None


def _parse_iso_datetime(value: Any):
    """Parse an ISO datetime for ordering only; return None when unavailable."""
    if not value:
        return None
    from datetime import datetime, timezone

    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    # Django USE_TZ responses are aware. If a defensive legacy payload is naive,
    # treat it as UTC so comparisons remain deterministic rather than crashing.
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def previous_canopy_after_baseline_reset(
    payload: dict[str, Any] | None,
    camera_config: dict[str, Any] | None,
) -> float | None:
    """Return previous valid canopy only when it belongs to the active baseline.

    ``growth_baseline_reset_at`` is stored on Camera by Backend. Historical
    CameraImage/ImageAnalysis rows remain immutable. When the newest valid
    analysis predates the reset timestamp, LeafyCV intentionally returns no
    previous canopy so the first valid image after the reset has
    ``growth_change = null`` and becomes the new baseline.

    If a reset exists but the previous analysis has no trustworthy captured_at,
    the conservative result is None; old history must never be pulled across a
    declared plant/layout change.
    """
    canopy = previous_canopy_from_latest(payload)
    if canopy is None:
        return None

    reset_value = (camera_config or {}).get("growth_baseline_reset_at")
    if not reset_value:
        return canopy

    reset_at = _parse_iso_datetime(reset_value)
    previous_at = _parse_iso_datetime(analysis_captured_at(payload))
    if reset_at is None:
        # Backend validation should prevent malformed values. Conservatively
        # disable cross-history growth rather than guessing.
        return None
    if previous_at is None or previous_at < reset_at:
        return None
    return canopy


def latest_analysis_camera_id(payload: dict[str, Any] | None) -> Any:
    """Extract Camera identity from an atomic latest-analysis response."""
    if not payload:
        return None
    if "camera_id" in payload:
        return payload.get("camera_id")
    image = payload.get("image")
    if isinstance(image, dict) and image.get("camera_id") is not None:
        return image.get("camera_id")
    analysis = payload.get("analysis")
    if isinstance(analysis, dict) and analysis.get("camera_id") is not None:
        return analysis.get("camera_id")
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
