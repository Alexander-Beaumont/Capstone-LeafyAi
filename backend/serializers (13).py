from rest_framework import serializers

from telemetry.models import (
    ActuatorStateObservation,
    BatchPlacement,
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


# Camera API serializers live in camera_capture.serializers.
# Re-export them here only for legacy/internal imports that have not yet moved.
from camera_capture.serializers import CameraImageSerializer, CameraSerializer


class SensorSerializer(serializers.ModelSerializer):
    # Preserve the richer internal sensor model while keeping the Farm Overview
    # frontend contract stable.
    sensor_type = serializers.SerializerMethodField()

    class Meta:
        model = Sensor
        fields = ["id", "device", "sensor_type", "unit"]

    def get_sensor_type(self, obj):
        aliases = {
            "water_temperature": "water_temp",
            "ambient_temperature": "ambient_temp",
        }
        return aliases.get(obj.sensor_type, obj.sensor_type)


class SensorReadingSerializer(serializers.ModelSerializer):
    timestamp = serializers.DateTimeField(source="measured_at", read_only=True)

    class Meta:
        model = SensorReading
        fields = ["id", "sensor", "timestamp", "value"]
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
