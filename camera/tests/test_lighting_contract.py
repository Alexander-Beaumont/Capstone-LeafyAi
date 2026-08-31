import numpy as np
import pytest

from camera.camera_collector import CameraCollector
from camera.lighting_client import LightingResult


class FakeBackend:
    def get_latest_image(self, camera_id):
        return None

    def upload_official_image(self, camera_id, jpeg_bytes, *, captured_at):
        assert jpeg_bytes == b"jpeg"
        return {"image_id": 99, "camera_id": camera_id}


class FakeLighting:
    def __init__(self):
        self.calls = []

    def set_state(self, state):
        self.calls.append(state)
        return LightingResult(True, state)


def test_lighting_restored_after_success(monkeypatch):
    lighting = FakeLighting()
    sleeps = []

    monkeypatch.setattr(
        "camera.camera_collector.capture_fresh_frame",
        lambda *args, **kwargs: np.zeros((10, 20, 3), dtype=np.uint8),
    )
    monkeypatch.setattr(
        "camera.camera_collector.encode_jpeg",
        lambda frame, jpeg_quality=92: b"jpeg",
    )

    collector = CameraCollector(
        FakeBackend(),
        lighting=lighting,
        pre_capture_light_off_seconds=2.0,
        post_capture_restore_seconds=1.0,
        sleep_fn=sleeps.append,
    )

    assert collector.process_camera({"id": 1, "enabled": True, "cv_enabled": True})
    assert lighting.calls == ["OFF", "ON"]
    assert sleeps == [2.0, 1.0]


def test_lighting_restored_when_capture_fails(monkeypatch):
    lighting = FakeLighting()
    sleeps = []

    def fail_capture(*args, **kwargs):
        raise RuntimeError("camera failed")

    monkeypatch.setattr("camera.camera_collector.capture_fresh_frame", fail_capture)

    collector = CameraCollector(
        FakeBackend(),
        lighting=lighting,
        pre_capture_light_off_seconds=2.0,
        post_capture_restore_seconds=1.0,
        sleep_fn=sleeps.append,
    )

    with pytest.raises(RuntimeError):
        collector._capture_official_jpeg({"id": 1, "source_type": "WEBCAM", "webcam_index": 0})

    assert lighting.calls == ["OFF", "ON"]
    # No post-capture delay is needed after a failed capture; restore immediately.
    assert sleeps == [2.0]
