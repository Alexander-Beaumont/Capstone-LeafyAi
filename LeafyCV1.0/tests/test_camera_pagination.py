from leafycv.api import BackendClient


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_get_cameras_follows_all_drf_pages(monkeypatch):
    client = BackendClient("http://backend")
    pages = {
        "/api/cameras/": {
            "results": [{"id": 1}],
            "next": "http://backend/api/cameras/?page=2",
        },
        "http://backend/api/cameras/?page=2": {
            "results": [{"id": 2}],
            "next": None,
        },
    }

    monkeypatch.setattr(
        client,
        "request",
        lambda method, path, **kwargs: FakeResponse(pages[path]),
    )
    assert [c["id"] for c in client.get_cameras()] == [1, 2]
