from rest_framework import serializers

from cv.models import (
    ImageAnalysis,
)


class ImageAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageAnalysis
        fields = [
            'id',
            'image',
            'created_at',
            'total_canopy_coverage',
            'growth_change',
            'crowding_percentage',
            'green_percentage',
            'yellow_percentage',
            'measurement_valid',
            'processing_time_ms',
            'vlm_ready',
            'quality_status',
            'quality_flags',
            'quality_message',
        ]

        read_only_fields = [
            'created_at',
        ]
