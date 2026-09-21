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

    def _effective(
        self,
        attrs,
        key,
        default=None,
    ):
        if key in attrs:
            return attrs[key]

        if self.instance is not None:
            return getattr(
                self.instance,
                key,
                default,
            )

        return default

    def validate(
        self,
        attrs,
    ):
        if attrs.get(
            "is_archived"
        ) is True:
            attrs["enabled"] = False

        source_type = str(
            self._effective(
                attrs,
                "source_type",
                "",
            )
            or ""
        ).upper()

        interval = self._effective(
            attrs,
            "capture_interval_minutes",
            30,
        )

        start = self._effective(
            attrs,
            "active_start_time",
        )

        end = self._effective(
            attrs,
            "active_end_time",
        )

        errors = {}

        try:
            if int(interval) < 1:
                errors[
                    "capture_interval_minutes"
                ] = (
                    "Must be at least 1 minute."
                )

        except (
            TypeError,
            ValueError,
        ):
            errors[
                "capture_interval_minutes"
            ] = (
                "Must be a positive integer."
            )

        if (
            (start is None)
            != (end is None)
        ):
            errors[
                "active_start_time"
            ] = (
                "Start and end must both "
                "be set, or both be blank "
                "for 24-hour capture."
            )

            errors[
                "active_end_time"
            ] = (
                "Start and end must both "
                "be set, or both be blank "
                "for 24-hour capture."
            )

        elif (
            start is not None
            and end is not None
            and start == end
        ):
            errors[
                "active_end_time"
            ] = (
                "Start and end cannot be equal. "
                "Use blank/blank for "
                "24-hour capture."
            )

        if source_type == "RTSP":
            ip = self._effective(
                attrs,
                "ip_address",
            )

            port = self._effective(
                attrs,
                "rtsp_port",
            )

            path = self._effective(
                attrs,
                "rtsp_path",
            )

            if not ip:
                errors[
                    "ip_address"
                ] = (
                    "RTSP cameras require "
                    "an IP address."
                )

            if not port:
                errors[
                    "rtsp_port"
                ] = (
                    "RTSP cameras require "
                    "a port."
                )

            if not path:
                errors[
                    "rtsp_path"
                ] = (
                    "RTSP cameras require "
                    "a stream path."
                )

        else:
            errors[
                "source_type"
            ] = (
                "Only RTSP cameras "
                "are supported."
            )

        if errors:
            raise serializers.ValidationError(
                errors
            )

        return attrs

class CameraImageSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = CameraImage

        fields = [
            "id",
            "camera",
            "captured_at",
            "path",
            "vlm_ready",
            "quality_status",
            "quality_flags",
            "quality_message",
            "quality_metrics",
        ]

        read_only_fields = fields


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
