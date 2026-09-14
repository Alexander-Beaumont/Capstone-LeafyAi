from camera_capture.backend_client import BackendClient


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
    seen = []

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

    def fake_request(method, path, **kwargs):
        seen.append(path)
        return FakeResponse(pages[path])

    monkeypatch.setattr(client, "request", fake_request)
    assert [c["id"] for c in client.get_cameras()] == [1, 2]
    assert seen == ["/api/cameras/", "http://backend/api/cameras/?page=2"]
