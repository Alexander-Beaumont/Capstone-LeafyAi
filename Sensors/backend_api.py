from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests


class DjangoBackend:
    def __init__(
        self,
        base_url: str,
        sensor_types: dict[str, str],
        *,
        username: str = "",
        password: str = "",
        access_token: str = "",
        refresh_token: str = "",
        timeout: float = 5.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.sensor_types = sensor_types
        self.username = username
        self.password = password
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.timeout = timeout
        self.sensor_ids: dict[str, int] = {}

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def _login(self) -> bool:
        if not self.username or not self.password:
            return False
        response = requests.post(
            f"{self.base_url}/api/auth/login/",
            json={"username": self.username, "password": self.password},
            timeout=self.timeout,
        )
        if not response.ok:
            return False
        payload = response.json()
        self.access_token = str(payload.get("access") or "")
        self.refresh_token = str(payload.get("refresh") or self.refresh_token)
        return bool(self.access_token)

    def _refresh(self) -> bool:
        if not self.refresh_token:
            return False
        response = requests.post(
            f"{self.base_url}/api/auth/refresh/",
            json={"refresh": self.refresh_token},
            timeout=self.timeout,
        )
        if not response.ok:
            return False
        self.access_token = str((response.json() or {}).get("access") or "")
        return bool(self.access_token)

    def request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        if not self.access_token:
            self._login()
        headers = dict(self._headers())
        headers.update(kwargs.pop("headers", {}) or {})
        response = requests.request(
            method,
            f"{self.base_url}{path}",
            headers=headers,
            timeout=self.timeout,
            **kwargs,
        )
        if response.status_code == 401 and (self._refresh() or self._login()):
            headers = dict(self._headers())
            headers.update(kwargs.pop("headers", {}) or {})
            response = requests.request(
                method,
                f"{self.base_url}{path}",
                headers=headers,
                timeout=self.timeout,
                **kwargs,
            )
        return response

    def discover_sensor_ids(self) -> dict[str, int]:
        response = self.request("GET", "/api/sensors/")
        response.raise_for_status()
        payload = response.json()
        rows = payload.get("results", []) if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            raise ValueError("GET /api/sensors/ returned an unexpected shape")
        by_type = {str(row.get("sensor_type")): int(row["id"]) for row in rows if isinstance(row, dict) and row.get("id")}
        missing = []
        for key, sensor_type in self.sensor_types.items():
            if sensor_type in by_type:
                self.sensor_ids[key] = by_type[sensor_type]
            else:
                missing.append(sensor_type)
        if missing:
            raise RuntimeError(f"Backend is missing seeded sensors: {', '.join(missing)}")
        return dict(self.sensor_ids)

    def map_data(self, water_data, ambient_data):
        if not self.sensor_ids:
            self.discover_sensor_ids()
        measured_at = datetime.now(timezone.utc).isoformat()
        return [
            {"sensor": self.sensor_ids["ph"], "value": water_data["ph"], "timestamp": measured_at},
            {"sensor": self.sensor_ids["ec"], "value": water_data["ec"], "timestamp": measured_at},
            {"sensor": self.sensor_ids["water_temp"], "value": water_data["water_temperature_c"], "timestamp": measured_at},
            {"sensor": self.sensor_ids["ambient_temp"], "value": ambient_data["ambient_temperature_c"], "timestamp": measured_at},
            {"sensor": self.sensor_ids["humidity"], "value": ambient_data["humidity_percent"], "timestamp": measured_at},
            {"sensor": self.sensor_ids["dew_point"], "value": ambient_data["dew_point_c"], "timestamp": measured_at},
            {"sensor": self.sensor_ids["water_level"], "value": ambient_data["water_level"], "timestamp": measured_at},
        ]

    def send_readings(self, readings):
        successes = 0
        for payload in readings:
            try:
                response = self.request("POST", "/api/sensor-readings/", json=payload)
                if response.status_code in (200, 201):
                    successes += 1
                else:
                    print(f"Sensor {payload['sensor']} rejected: {response.status_code} {response.text}")
            except requests.RequestException as exc:
                print(f"Sensor {payload['sensor']} transport error: {exc}")
        print(f"Sensor batch: {successes}/{len(readings)} readings stored.")
        return successes
