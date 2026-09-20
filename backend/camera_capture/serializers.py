from rest_framework import serializers

from telemetry.models import Camera, CameraImage, FarmLevel


class CameraSerializer(serializers.ModelSerializer):
    """Public Camera API serializer.

    The model relation stays ``farm_level`` internally while the API exposes
    the locked public field name ``farm_level_id``.
    """

    farm_level_id = serializers.PrimaryKeyRelatedField(
        source="farm_level",
        queryset=FarmLevel.objects.all(),
    )

    class Meta:
        model = Camera
        fields = [
            "id",
            "farm_level_id",
            "name",
            "position",
            "source_type",
            "ip_address",
            "rtsp_port",
            "rtsp_path",
            "enabled",
            "is_archived",
            "capture_interval_minutes",
            "active_start_time",
            "active_end_time",
        ]

    def _effective(self, attrs, key, default=None):
        if key in attrs:
            return attrs[key]
        if self.instance is not None:
            return getattr(self.instance, key, default)
        return default

    def validate(self, attrs):
        if attrs.get("is_archived") is True:
            attrs["enabled"] = False

        source_type = str(self._effective(attrs, "source_type", "") or "").upper()
        interval = self._effective(attrs, "capture_interval_minutes", 30)
        start = self._effective(attrs, "active_start_time")
        end = self._effective(attrs, "active_end_time")

        errors = {}
        try:
            if int(interval) < 1:
                errors["capture_interval_minutes"] = "Must be at least 1 minute."
        except (TypeError, ValueError):
            errors["capture_interval_minutes"] = "Must be a positive integer."

        if (start is None) != (end is None):
            message = (
                "Start and end must both be set, or both be blank for "
                "24-hour capture."
            )
            errors["active_start_time"] = message
            errors["active_end_time"] = message
        elif start is not None and end is not None and start == end:
            errors["active_end_time"] = (
                "Start and end cannot be equal. Use blank/blank for 24-hour capture."
            )

        if source_type == "RTSP":
            if not self._effective(attrs, "ip_address"):
                errors["ip_address"] = "RTSP cameras require an IP address."
            if not self._effective(attrs, "rtsp_port"):
                errors["rtsp_port"] = "RTSP cameras require a port."
            if not self._effective(attrs, "rtsp_path"):
                errors["rtsp_path"] = "RTSP cameras require a stream path."
        else:
            errors["source_type"] = "Only RTSP cameras are supported."

        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class CameraImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    quality_reason = serializers.SerializerMethodField()

    class Meta:
        model = CameraImage
        fields = [
            "id",
            "camera",
            "captured_at",
            "path",
            "image_url",
            "quality_status",
            "quality_reason",
        ]
        read_only_fields = fields

    def get_image_url(self, obj):
        try:
            request = self.context.get("request")
            url = obj.path.url
            return request.build_absolute_uri(url) if request else url
        except (ValueError, AttributeError):
            return ""

    def get_quality_reason(self, obj):
        if str(obj.quality_status or "").upper() == "FAIL":
            return obj.quality_message
        return None
