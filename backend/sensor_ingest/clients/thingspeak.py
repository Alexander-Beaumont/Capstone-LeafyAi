import logging

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from sensor_ingest.exceptions import (
    SourceAuthenticationError,
    SourcePayloadError,
    SourceTransportError,
)


logger = logging.getLogger(__name__)


class ThingSpeakClient:
    """Small, testable HTTP adapter for the ThingSpeak read API."""

    BASE_URL = "https://api.thingspeak.com"

    def __init__(
        self,
        *,
        channel_id,
        read_api_key,
        connect_timeout_seconds=3.05,
        read_timeout_seconds=10,
        retry_total=4,
        backoff_factor=0.5,
        session=None,
    ):
        self.channel_id = str(channel_id)
        self.timeout = (
            float(connect_timeout_seconds),
            float(read_timeout_seconds),
        )
        self.session = session or requests.Session()

        self.session.headers.update(
            {
                "THINGSPEAKAPIKEY": read_api_key,
                "User-Agent": "LeafyAI-SensorIngest/1.0",
                "Accept": "application/json",
            }
        )

        # GET is safe to retry.  The API key is carried in a header so it does
        # not appear in request URLs or ordinary URL logs.
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
        self.session.mount("https://", adapter)

    def _get_json(self, path, *, params=None):
        url = f"{self.BASE_URL}{path}"
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
        except requests.RequestException as exc:
            raise SourceTransportError(
                f"ThingSpeak request failed: {exc.__class__.__name__}"
            ) from exc

        if response.status_code in (401, 403):
            raise SourceAuthenticationError(
                f"ThingSpeak rejected credentials (HTTP {response.status_code})."
            )

        try:
            response.raise_for_status()
        except requests.RequestException as exc:
            raise SourceTransportError(
                f"ThingSpeak returned HTTP {response.status_code}."
            ) from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise SourcePayloadError("ThingSpeak returned non-JSON data.") from exc

        # ThingSpeak documents a body of -1 when a channel cannot be read;
        # this can occur even with HTTP 200, so status code alone is not enough
        # to distinguish an authentication/access failure.
        if payload == -1 or payload == "-1":
            raise SourceAuthenticationError(
                "ThingSpeak denied access to the requested channel."
            )

        return payload

    def get_latest(self):
        return self._get_json(
            f"/channels/{self.channel_id}/feeds/last.json"
        )

    def get_recent(self, *, results=100):
        payload = self._get_json(
            f"/channels/{self.channel_id}/feeds.json",
            params={"results": int(results)},
        )
        feeds = payload.get("feeds") if isinstance(payload, dict) else None
        if not isinstance(feeds, list):
            raise SourcePayloadError(
                "ThingSpeak history response does not contain a feeds list."
            )
        return feeds
