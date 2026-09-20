"""HTTP client for the two physical Lab sensor endpoints.

This sits beside the existing ThingSpeak client rather than replacing it.  The
collector can therefore preserve the team's ingestion architecture while using
the direct ESP32 endpoints in the Lab.
"""
from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from sensor_ingest.exceptions import SourcePayloadError, SourceTransportError


class LabHTTPClient:
    def __init__(
        self,
        *,
        timeout_seconds: float = 5.0,
        retry_total: int = 3,
        backoff_factor: float = 0.5,
        session=None,
    ):
        self.timeout = float(timeout_seconds)
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "LeafyAI-LabSensorIngest/1.0",
                "Accept": "application/json",
            }
        )
        retry = Retry(
            total=int(retry_total),
            connect=int(retry_total),
            read=int(retry_total),
            status=int(retry_total),
            backoff_factor=float(backoff_factor),
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET"]),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def get_json(self, url: str, *, label: str) -> dict:
        if not str(url or "").strip():
            return {}
        try:
            response = self.session.get(str(url).strip(), timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise SourceTransportError(
                f"{label} endpoint request failed: {exc.__class__.__name__}"
            ) from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise SourcePayloadError(
                f"{label} endpoint returned non-JSON data."
            ) from exc

        if not isinstance(payload, dict):
            raise SourcePayloadError(
                f"{label} endpoint returned a non-object JSON payload."
            )
        return payload
