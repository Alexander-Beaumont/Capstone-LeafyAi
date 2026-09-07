from rest_framework import serializers

from telemetry.models import (
    ActuatorStateObservation,
    BatchPlacement,
    Camera,
    CameraImage,
    Doser,
    Farm,
    FarmDevice,
    FarmLevel,
    GrowingArea,
    NutrientTank,
    PlantBatch,
    SafeRange,
    Sensor,
    SensorReading,
    SetpointObservation,
)


class FarmSerializer(serializers.ModelSerializer):
    class Meta:
        model = Farm
        fields = ["id", "name", "location"]


class FarmDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmDevice
        fields = ["id", "farm", "name", "slug", "device_type"]


class FarmLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmLevel
        fields = ["id", "device", "level_number"]


class GrowingAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrowingArea
        fields = ["id", "farm_level", "name", "slot_count"]


class PlantBatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlantBatch
        fields = [
            "id",
            "plant_type",
            "planting_date",
            "growth_stage",
            "status",
        ]


class BatchPlacementSerializer(serializers.ModelSerializer):
    class Meta:
        model = BatchPlacement
        fields = ["id", "plant_batch", "growing_area", "start_date", "end_date"]


class CameraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Camera
        fields = [
            "id",
            "farm_level",
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
            "capture_interval_minutes",
            "active_start_time",
            "active_end_time",
            "growth_baseline_reset_at",
        ]


class CameraImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CameraImage
        fields = ["id", "camera", "captured_at", "path"]
        read_only_fields = ["captured_at"]


class SensorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sensor
        fields = [
            "id",
            "device",
            "slug",
            "sensor_type",
            "unit",
            "enabled",
            "expected_interval_seconds",
            "stale_after_seconds",
        ]


class SensorReadingSerializer(serializers.ModelSerializer):
    sensor_slug = serializers.CharField(source="sensor.slug", read_only=True)
    sensor_type = serializers.CharField(source="sensor.sensor_type", read_only=True)
    unit = serializers.CharField(source="sensor.unit", read_only=True)

    class Meta:
        model = SensorReading
        fields = [
            "id",
            "sensor",
            "sensor_slug",
            "sensor_type",
            "unit",
            "value",
            "measured_at",
            "received_at",
            "source",
            "source_channel_id",
            "source_entry_id",
            "quality_status",
            "quality_notes",
        ]
        read_only_fields = fields


class ActuatorStateObservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActuatorStateObservation
        fields = [
            "id",
            "device",
            "actuator_slug",
            "state",
            "measured_at",
            "received_at",
            "source",
            "source_channel_id",
            "source_entry_id",
            "quality_status",
            "quality_notes",
        ]
        read_only_fields = fields


class SetpointObservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SetpointObservation
        fields = [
            "id",
            "device",
            "setpoint_slug",
            "value",
            "unit",
            "measured_at",
            "received_at",
            "source",
            "source_channel_id",
            "source_entry_id",
            "quality_status",
            "quality_notes",
        ]
        read_only_fields = fields


class NutrientTankSerializer(serializers.ModelSerializer):
    class Meta:
        model = NutrientTank
        fields = [
            "id",
            "device",
            "capacity_l",
            "current_level_l",
            "last_refill_date",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]


class DoserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doser
        fields = [
            "id",
            "device",
            "chemical_type",
            "concentration",
            "flow_rate_ml_per_min",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]


class SafeRangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafeRange
        fields = ["id", "sensor_type", "min_value", "max_value", "severity"]
