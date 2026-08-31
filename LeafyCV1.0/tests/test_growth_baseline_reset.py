from leafycv.api import previous_canopy_after_baseline_reset


def _payload(captured_at, canopy=40.0):
    return {
        "camera_id": 1,
        "image_id": 10,
        "captured_at": captured_at,
        "analysis": {"total_canopy_coverage": canopy},
    }


def test_no_reset_uses_previous_valid_canopy():
    assert previous_canopy_after_baseline_reset(
        _payload("2026-08-28T10:00:00+10:00"), {}
    ) == 40.0


def test_previous_analysis_before_reset_is_ignored():
    cfg = {"growth_baseline_reset_at": "2026-08-28T10:05:00+10:00"}
    assert previous_canopy_after_baseline_reset(
        _payload("2026-08-28T10:00:00+10:00"), cfg
    ) is None


def test_first_post_reset_valid_analysis_becomes_usable_baseline():
    cfg = {"growth_baseline_reset_at": "2026-08-28T10:05:00+10:00"}
    assert previous_canopy_after_baseline_reset(
        _payload("2026-08-28T10:30:00+10:00", canopy=20.0), cfg
    ) == 20.0


def test_reset_with_missing_previous_timestamp_is_conservative():
    cfg = {"growth_baseline_reset_at": "2026-08-28T10:05:00+10:00"}
    payload = {"analysis": {"total_canopy_coverage": 55.0}}
    assert previous_canopy_after_baseline_reset(payload, cfg) is None


def test_timezone_offsets_compare_by_absolute_time():
    cfg = {"growth_baseline_reset_at": "2026-08-28T10:05:00+10:00"}
    # 00:10 UTC == 10:10 Melbourne standard time, so this is post-reset.
    assert previous_canopy_after_baseline_reset(
        _payload("2026-08-28T00:10:00+00:00", canopy=21.0), cfg
    ) == 21.0
