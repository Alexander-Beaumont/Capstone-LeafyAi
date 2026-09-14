from leafycv.api import latest_analysis_camera_id, latest_analysis_image_id, previous_canopy_from_latest


def test_previous_canopy_nested_analysis():
    payload = {"analysis": {"total_canopy_coverage": "63.4"}}
    assert previous_canopy_from_latest(payload) == 63.4


def test_latest_analysis_image_id():
    assert latest_analysis_image_id({"image_id": 152}) == 152
    assert latest_analysis_image_id({"image": {"image_id": 153}}) == 153
    assert latest_analysis_image_id(None) is None


def test_latest_analysis_camera_id():
    assert latest_analysis_camera_id({"camera_id": 1}) == 1
    assert latest_analysis_camera_id({"image": {"camera_id": 2}}) == 2
    assert latest_analysis_camera_id(None) is None
