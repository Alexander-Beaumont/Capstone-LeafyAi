from leafycv.api import previous_canopy_from_latest, latest_analysis_image_id


def test_previous_canopy_nested():
    payload = {
        "image_id": 4,
        "analysis": {
            "total_canopy_coverage": 31.5,
            "measurement_valid": True,
        },
    }
    assert previous_canopy_from_latest(payload) == 31.5
    assert latest_analysis_image_id(payload) == 4


def test_invalid_analysis_is_not_growth_baseline():
    payload = {
        "image_id": 5,
        "analysis": {
            "total_canopy_coverage": 8.0,
            "measurement_valid": False,
        },
    }
    assert previous_canopy_from_latest(payload) is None
