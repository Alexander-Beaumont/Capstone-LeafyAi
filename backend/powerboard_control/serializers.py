from rest_framework import serializers

from .models import PowerboardConfiguration


class PowerboardConfigurationSerializer(serializers.ModelSerializer):
    farm_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = PowerboardConfiguration
        fields = [
            "farm_id",
            "powerboard_1_ip",
            "powerboard_2_ip",
            "updated_at",
        ]
        read_only_fields = ["farm_id", "updated_at"]
