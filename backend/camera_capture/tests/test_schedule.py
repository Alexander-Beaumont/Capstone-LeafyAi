from datetime import datetime
from zoneinfo import ZoneInfo

from camera_capture.camera_collector import capture_decision


ZONE = "Australia/Melbourne"


def _camera(interval=30, start="06:00:00", end="20:00:00", camera_id=1):
    return {
        "id": camera_id,
        "enabled": True,
        "cv_enabled": True,
        "capture_interval_minutes": interval,
        "active_start_time": start,
        "active_end_time": end,
    }


def test_new_camera_is_due_immediately_inside_window():
    now = datetime(2026, 8, 20, 12, 17, tzinfo=ZoneInfo(ZONE))
    decision = capture_decision(_camera(), None, now_local=now, timezone_name=ZONE)
    assert decision.due
    assert decision.reason == "no previous official image"


def test_outside_active_hours_skips():
    now = datetime(2026, 8, 20, 23, 0, tzinfo=ZoneInfo(ZONE))
    assert not capture_decision(_camera(), None, now_local=now, timezone_name=ZONE).due


def test_interval_is_measured_from_latest_official_image():
    camera = _camera(interval=30)
    latest = {"camera_id": 1, "captured_at": "2026-08-20T12:00:00+10:00"}

    before_due = datetime(2026, 8, 20, 12, 29, 59, tzinfo=ZoneInfo(ZONE))
    decision = capture_decision(camera, latest, now_local=before_due, timezone_name=ZONE)
    assert not decision.due

    after_due = datetime(2026, 8, 20, 12, 30, 1, tzinfo=ZoneInfo(ZONE))
    decision = capture_decision(camera, latest, now_local=after_due, timezone_name=ZONE)
    assert decision.due
    assert decision.due_at.isoformat().startswith("2026-08-20T12:30:00")


def test_offline_period_produces_one_overdue_capture_not_backfill():
    camera = _camera(interval=30)
    latest = {"camera_id": 1, "captured_at": "2026-08-20T10:00:00+10:00"}
    restarted = datetime(2026, 8, 20, 12, 10, tzinfo=ZoneInfo(ZONE))

    decision = capture_decision(camera, latest, now_local=restarted, timezone_name=ZONE)
    assert decision.due
    # The due_at shows the interval first became overdue. The collector still
    # captures only one image now; it never creates historical 10:30/11:00/etc.
    assert decision.due_at.isoformat().startswith("2026-08-20T10:30:00")


def test_after_restart_capture_next_due_is_based_on_actual_new_image():
    camera = _camera(interval=30)
    latest_after_restart = {
        "camera_id": 1,
        "captured_at": "2026-08-20T12:10:00+10:00",
    }

    at_1239 = datetime(2026, 8, 20, 12, 39, 59, tzinfo=ZoneInfo(ZONE))
    assert not capture_decision(
        camera, latest_after_restart, now_local=at_1239, timezone_name=ZONE
    ).due

    at_1240 = datetime(2026, 8, 20, 12, 40, 0, tzinfo=ZoneInfo(ZONE))
    assert capture_decision(
        camera, latest_after_restart, now_local=at_1240, timezone_name=ZONE
    ).due


def test_overnight_window_is_only_an_eligibility_gate():
    camera = _camera(interval=60, start="20:00:00", end="06:00:00")
    latest = {"camera_id": 1, "captured_at": "2026-08-21T01:00:00+10:00"}

    inside = datetime(2026, 8, 21, 2, 0, 5, tzinfo=ZoneInfo(ZONE))
    assert capture_decision(camera, latest, now_local=inside, timezone_name=ZONE).due

    outside = datetime(2026, 8, 21, 12, 0, tzinfo=ZoneInfo(ZONE))
    assert not capture_decision(camera, latest, now_local=outside, timezone_name=ZONE).due


def test_same_next_day_window_can_naturally_realign_overdue_cameras():
    now = datetime(2026, 8, 21, 6, 0, 10, tzinfo=ZoneInfo(ZONE))
    camera_1 = _camera(interval=30, start="06:00:00", end="22:00:00", camera_id=1)
    camera_2 = _camera(interval=60, start="06:00:00", end="22:00:00", camera_id=2)

    latest_1 = {"camera_id": 1, "captured_at": "2026-08-20T21:40:00+10:00"}
    latest_2 = {"camera_id": 2, "captured_at": "2026-08-20T21:00:00+10:00"}

    assert capture_decision(camera_1, latest_1, now_local=now, timezone_name=ZONE).due
    assert capture_decision(camera_2, latest_2, now_local=now, timezone_name=ZONE).due


def test_latest_image_camera_identity_mismatch_is_rejected():
    now = datetime(2026, 8, 20, 12, 30, tzinfo=ZoneInfo(ZONE))
    latest_wrong_camera = {
        "camera_id": 2,
        "captured_at": "2026-08-20T12:00:00+10:00",
    }

    try:
        capture_decision(
            _camera(camera_id=1),
            latest_wrong_camera,
            now_local=now,
            timezone_name=ZONE,
        )
    except ValueError as exc:
        assert "camera mismatch" in str(exc)
    else:
        raise AssertionError("Expected camera identity mismatch to raise ValueError")
