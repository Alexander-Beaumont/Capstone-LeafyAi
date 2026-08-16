from rest_framework import serializers

from computer_vision.models import (
    ImageAnalysis,
    PlantVisionMeasurement,
)


class ImageAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageAnalysis
        fields = [
            'id',
            'image',
            'created_at',
            'total_canopy_coverage',
            'visible_plant_count',
            'measurement_valid',
            'processing_time_ms',
        ]

        read_only_fields = [
            'created_at',
        ]


class PlantVisionMeasurementSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlantVisionMeasurement
        fields = [
            'id',
            'image_analysis',
            'slot',
            'canopy_coverage',
            'width_px',
            'height_px',
            'width_cm',
            'height_cm',
            'green_percentage',
            'yellow_percentage',
            'crowding_percentage',
            'growth_stage',
            'growth_change',
            'visible',
            'measurement_valid',
            'created_at',
        ]

        read_only_fields = [
            'created_at',
        ]