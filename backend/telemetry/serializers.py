from rest_framework import serializers
from telemetry.models import (
    Farm,
    FarmDevice,
    FarmLevel,
    GrowingArea,
    PlantBatch,
    BatchPlacement,
    Camera,
    CameraImage,
    Sensor,
    SensorReading,
    NutrientTank,
    Doser,
    SafeRange,
)

class FarmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farm
        fields = [
            'id',
            'name',
            'location',
        ]
class FarmDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmDevice
        fields = [
            'id',
            'farm',
            'name',
            'device_type',
        ]
class FarmLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmLevel
        fields = [
            'id',
            'device',
            'level_number',
        ]

class GrowingAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrowingArea
        fields = [
            'id',
            'farm_level',
            'name',
            'slot_count',
        ]
class PlantBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlantBatch
        fields = [
            'id',
            'plant_type',
            'planting_date',
            'growth_stage',
            'status',
        ]
class BatchPlacementSerializer(serializers.ModelSerializer):
    class Meta:
        model = BatchPlacement
        fields = [
            'id',
            'plant_batch',
            'growing_area',
            'start_date',
            'end_date',
        ]
class CameraSerializer(serializers.ModelSerializer):
    # FINAL LOCKED Camera API contract exposes the FarmLevel foreign key as
    # `farm_level_id`. The Django model relation remains `farm_level`.
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
            "webcam_index",
            "roi_points",
            "enabled",
            "cv_enabled",
            "is_archived",
            "capture_interval_minutes",
            "active_start_time",
            "active_end_time",
            "growth_baseline_reset_at",
        ]

    def _effective(self, attrs, key, default=None):
        if key in attrs:
            return attrs[key]
        if self.instance is not None:
            return getattr(self.instance, key, default)
        return default

    def validate_roi_points(self, value):
        if value is None:
            return None
        if not isinstance(value, dict):
            raise serializers.ValidationError("ROI must be an object with x, y, width and height.")
        required = ("x", "y", "width", "height")
        missing = [key for key in required if key not in value]
        if missing:
            raise serializers.ValidationError(f"ROI is missing: {', '.join(missing)}")
        try:
            x, y, width, height = (float(value[key]) for key in required)
        except (TypeError, ValueError):
            raise serializers.ValidationError("ROI x, y, width and height must be numeric.")
        if not (0 <= x < 1 and 0 <= y < 1):
            raise serializers.ValidationError("ROI x and y must be normalized values in [0, 1).")
        if width <= 0 or height <= 0:
            raise serializers.ValidationError("ROI width and height must be greater than 0.")
        if x + width > 1 or y + height > 1:
            raise serializers.ValidationError("ROI must stay inside the image boundary.")
        return {"x": x, "y": y, "width": width, "height": height}

    def validate(self, attrs):
        if attrs.get("is_archived") is True:
            attrs["enabled"] = False
            attrs["cv_enabled"] = False

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
            errors["active_start_time"] = "Start and end must both be set, or both be blank for 24-hour capture."
            errors["active_end_time"] = "Start and end must both be set, or both be blank for 24-hour capture."
        elif start is not None and end is not None and start == end:
            errors["active_end_time"] = "Start and end cannot be equal. Use blank/blank for 24-hour capture."

        if source_type == "RTSP":
            ip = self._effective(attrs, "ip_address")
            port = self._effective(attrs, "rtsp_port")
            path = self._effective(attrs, "rtsp_path")
            if not ip:
                errors["ip_address"] = "RTSP cameras require an IP address."
            if not port:
                errors["rtsp_port"] = "RTSP cameras require a port."
            if not path:
                errors["rtsp_path"] = "RTSP cameras require a stream path."
            if "source_type" in attrs:
                attrs["webcam_index"] = None
        elif source_type == "WEBCAM":
            index = self._effective(attrs, "webcam_index")
            if index is None:
                errors["webcam_index"] = "WEBCAM cameras require webcam_index."
            if "source_type" in attrs:
                attrs["ip_address"] = None
                attrs["rtsp_port"] = None
                attrs["rtsp_path"] = None
        else:
            errors["source_type"] = "Must be RTSP or WEBCAM."

        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class CameraImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CameraImage
        fields = ["id", "camera", "captured_at", "path"]
        read_only_fields = ["id", "camera", "captured_at", "path"]


class SensorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sensor
        fields = [
            'id',
            'device',
            'sensor_type',
            'unit',
        ]

class SensorReadingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorReading
        fields = [
            'id',
            'sensor',
            'timestamp',
            'value',
        ]

        read_only_fields = [
            'timestamp',
        ]
class NutrientTankSerializer(serializers.ModelSerializer):
    class Meta:
        model = NutrientTank
        fields = [
            'id',
            'device',
            'capacity_l',
            'current_level_l',
            'last_refill_date',
            'updated_at',
        ]

        read_only_fields = [
            'updated_at',
        ]
class DoserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doser
        fields = [
            'id',
            'device',
            'chemical_type',
            'concentration',
            'flow_rate_ml_per_min',
            'updated_at',
        ]

        read_only_fields = [
            'updated_at',
        ]
class SafeRangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafeRange
        fields = [
            'id',
            'sensor_type',
            'min_value',
            'max_value',
            'severity',
        ]
