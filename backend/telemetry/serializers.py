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
<<<<<<< HEAD
        model = Farm                                                                                                            
        fields = ['id', 'name', 'location']


=======
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
>>>>>>> f504721e64d9aad837c24599c8aed59986118f4a
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
            'rtsp_path',
            'webcam_index',
            'roi_points',
            'enabled',
            'cv_enabled',
            'capture_interval_minutes',
            'active_start_time',
            'active_end_time',
            'growth_baseline_reset_at',
        ]
class CameraImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CameraImage
<<<<<<< HEAD
        fields = ['id', 'camera', 'timestamp']  # , 'image']  # Uncomment 'image' if using ImageField
=======
        fields = [
            'id',
            'camera',
            'captured_at',
            'path',
        ]

        read_only_fields = [
            'captured_at',
        ]
>>>>>>> f504721e64d9aad837c24599c8aed59986118f4a


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
