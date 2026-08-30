from leafycv.api import BackendClient


class FakeResponse:
    status_code = 200

    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class FakeClient(BackendClient):
    def __init__(self, payload):
        super().__init__("http://example.test")
        self.payload = payload

    def request(self, method, path_or_url, **kwargs):
        assert method == "GET"
        assert path_or_url == "/api/cameras/"
        return FakeResponse(self.payload)


def test_get_cameras_supports_plain_list():
    client = FakeClient([{"id": 1}, {"id": 2}])
    assert [c["id"] for c in client.get_cameras()] == [1, 2]


def test_get_cameras_supports_drf_pagination():
    client = FakeClient({"count": 2, "results": [{"id": 1}, {"id": 2}]})
    assert [c["id"] for c in client.get_cameras()] == [1, 2]
