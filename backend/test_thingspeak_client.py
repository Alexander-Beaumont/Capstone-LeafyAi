from django.test import SimpleTestCase

from sensor_ingest.clients.thingspeak import ThingSpeakClient
from sensor_ingest.exceptions import SourceAuthenticationError, SourcePayloadError
from sensor_ingest.tests.fixtures import VALID_ENTRY


class FakeResponse:
    def __init__(self, *, status_code=200, payload=None, json_error=False):
        self.status_code = status_code
        self._payload = payload
        self._json_error = json_error

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests

            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        if self._json_error:
            raise ValueError("bad json")
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.headers = {}
        self.requests = []
        self.mounted = []

    def mount(self, prefix, adapter):
        self.mounted.append((prefix, adapter))

    def get(self, url, *, params=None, timeout=None):
        self.requests.append({"url": url, "params": params, "timeout": timeout})
        return self.responses.pop(0)


class ThingSpeakClientTests(SimpleTestCase):
    def test_api_key_is_sent_in_header_not_url(self):
        session = FakeSession([FakeResponse(payload=VALID_ENTRY)])
        client = ThingSpeakClient(
            channel_id="123",
            read_api_key="secret-key",
            session=session,
        )
        payload = client.get_latest()
        self.assertEqual(payload["entry_id"], 12345)
        self.assertEqual(session.headers["THINGSPEAKAPIKEY"], "secret-key")
        self.assertNotIn("secret-key", session.requests[0]["url"])

    def test_history_requires_feeds_list(self):
        session = FakeSession([FakeResponse(payload={"unexpected": []})])
        client = ThingSpeakClient(
            channel_id="123",
            read_api_key="secret-key",
            session=session,
        )
        with self.assertRaises(SourcePayloadError):
            client.get_recent(results=100)

    def test_authentication_failure_has_specific_exception(self):
        session = FakeSession([FakeResponse(status_code=403, payload={})])
        client = ThingSpeakClient(
            channel_id="123",
            read_api_key="secret-key",
            session=session,
        )
        with self.assertRaises(SourceAuthenticationError):
            client.get_latest()

    def test_http_200_minus_one_is_treated_as_access_failure(self):
        session = FakeSession([FakeResponse(payload=-1)])
        client = ThingSpeakClient(
            channel_id="123",
            read_api_key="bad-key",
            session=session,
        )
        with self.assertRaises(SourceAuthenticationError):
            client.get_latest()
