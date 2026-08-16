from rest_framework import serializers
from telemetry.models import (
    Farm,
    FarmDevice,
    FarmLevel,
    GrowingArea,
    Slot,
    PlantBatch,
    BatchPlacement,
    Camera,
    CameraSlotPosition,
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
class SlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slot
        fields = [
            'id',
            'growing_area',
            'slot_number',
            'row',
            'column',
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
    class Meta:
        model = Camera
        fields = [
            'id',
            'farm_level',
            'name',
            'position',
            'source_type',
            'ip_address',
            'rtsp_port',
            'rtsp_path'
            'webcam_index',
            'lighting_mode',
            'roi_points',
            'calibration_start_x',
            'calibration_start_y',
            'calibration_end_x',
            'calibration_end_y',
            'calibration_length_cm',
            'enabled',
        ]
class CameraSlotPositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CameraSlotPosition
        fields = [
            'id',
            'camera',
            'slot',
            'centre_x',
            'centre_y',
            'created_at',
            'updated_at',
        ]

        read_only_fields = [
            'created_at',
            'updated_at',
        ]

class CameraImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CameraImage
        fields = [
            'id',
            'camera',
            'timestamp',
            'path',
        ]

        read_only_fields = [
            'timestamp',
        ]


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
