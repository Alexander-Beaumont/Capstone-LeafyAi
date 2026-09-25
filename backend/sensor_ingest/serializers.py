import ipaddress
from urllib.parse import urlsplit

from rest_framework import serializers

from sensor_ingest.models import SensorIngestConfiguration
from sensor_ingest.services.configuration import propagate_sensor_timing


def validate_lan_url(value):
    if not value:
        return value
    try:
        parsed = urlsplit(value)
        address = ipaddress.ip_address(parsed.hostname or "")
    except ValueError as exc:
        raise serializers.ValidationError(
            "Use a literal private LAN IP address (for example http://192.168.1.20/readings)."
        ) from exc
    if parsed.scheme not in {"http", "https"}:
        raise serializers.ValidationError("Only HTTP and HTTPS endpoints are allowed.")
    if parsed.username is not None or parsed.password is not None:
        raise serializers.ValidationError("Credentials must not be embedded in endpoint URLs.")
    if parsed.fragment:
        raise serializers.ValidationError("Endpoint URLs must not contain fragments.")
    if not (address.is_private or address.is_loopback or address.is_link_local):
        raise serializers.ValidationError("The endpoint must use a private LAN address.")
    return value


class SensorIngestConfigurationSerializer(serializers.ModelSerializer):
    device_id = serializers.IntegerField(source="device.id", read_only=True)
    device_name = serializers.CharField(source="device.name", read_only=True)
    device_slug = serializers.CharField(source="device.slug", read_only=True)
    farm_id = serializers.IntegerField(source="device.farm_id", read_only=True)

    class Meta:
        model = SensorIngestConfiguration
        fields = [
            "id", "farm_id", "device_id", "device_name", "device_slug", "enabled",
            "water_quality_url", "ambient_sensor_url", "poll_interval_seconds",
            "sensor_stale_threshold_seconds", "last_attempt_at", "last_success_at",
            "last_error", "consecutive_failures", "updated_at",
        ]
        read_only_fields = [
            "id", "farm_id", "device_id", "device_name", "device_slug",
            "last_attempt_at", "last_success_at", "last_error",
            "consecutive_failures", "updated_at",
        ]

    def validate_water_quality_url(self, value):
        return validate_lan_url(value)

    def validate_ambient_sensor_url(self, value):
        return validate_lan_url(value)

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        propagate_sensor_timing(instance)
        return instance
