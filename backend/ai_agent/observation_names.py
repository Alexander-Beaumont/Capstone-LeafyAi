def attach_camera_names(observations, camera_names):
    """Add trusted database camera names to model-produced observations."""

    result = []
    for observation in observations or []:
        if not isinstance(observation, dict):
            result.append(observation)
            continue
        item = dict(observation)
        camera_id = item.get("camera_id")
        try:
            normalized_id = int(camera_id)
        except (TypeError, ValueError):
            normalized_id = None
        if normalized_id in camera_names:
            item["camera_id"] = normalized_id
            item["camera_name"] = camera_names[normalized_id]
        result.append(item)
    return result
