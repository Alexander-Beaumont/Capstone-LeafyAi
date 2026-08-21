from datetime import datetime
from zoneinfo import ZoneInfo

from camera.camera_collector import capture_decision


ZONE = "Australia/Melbourne"


def test_first_image_is_due():
    camera = {
        "enabled": True,
        "cv_enabled": True,
        "capture_interval_minutes": 30,
        "active_start_time": "06:00:00",
        "active_end_time": "20:00:00",
    }
    now = datetime(2026, 8, 20, 12, 0, tzinfo=ZoneInfo(ZONE))
    assert capture_decision(camera, None, now_local=now, timezone_name=ZONE).due


def test_outside_active_hours_skips():
    camera = {
        "enabled": True,
        "cv_enabled": True,
        "capture_interval_minutes": 30,
        "active_start_time": "06:00:00",
        "active_end_time": "20:00:00",
    }
    now = datetime(2026, 8, 20, 23, 0, tzinfo=ZoneInfo(ZONE))
    assert not capture_decision(camera, None, now_local=now, timezone_name=ZONE).due


def test_interval_not_elapsed():
    camera = {
        "enabled": True,
        "cv_enabled": True,
        "capture_interval_minutes": 30,
        "active_start_time": None,
        "active_end_time": None,
    }
    now = datetime(2026, 8, 20, 12, 20, tzinfo=ZoneInfo(ZONE))
    latest = {"captured_at": "2026-08-20T12:00:00+10:00"}
    assert not capture_decision(camera, latest, now_local=now, timezone_name=ZONE).due
