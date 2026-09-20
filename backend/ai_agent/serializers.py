from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from rest_framework import serializers

from ai_agent.credentials import encrypt_api_key, mask_api_key
from ai_agent.models import AIConfiguration, AIDecision, AIRecommendationRun, FarmAction, KasaActuator, SafetyCheck


class AIConfigurationSerializer(serializers.ModelSerializer):
    llm_api_key = serializers.CharField(write_only=True, required=False, allow_blank=True)
    vlm_api_key = serializers.CharField(write_only=True, required=False, allow_blank=True)
    clear_llm_api_key = serializers.BooleanField(write_only=True, required=False, default=False)
    clear_vlm_api_key = serializers.BooleanField(write_only=True, required=False, default=False)
    llm_api_key_configured = serializers.SerializerMethodField()
    vlm_api_key_configured = serializers.SerializerMethodField()
    llm_api_key_mask = serializers.SerializerMethodField()
    vlm_api_key_mask = serializers.SerializerMethodField()

    class Meta:
        model = AIConfiguration
        fields = [
            "farm", "llm_provider", "llm_model", "llm_api_key", "llm_api_key_configured", "llm_api_key_mask",
            "vlm_provider", "vlm_model", "vlm_api_key", "vlm_api_key_configured", "vlm_api_key_mask",
            "clear_llm_api_key", "clear_vlm_api_key", "schedule_enabled", "timezone", "interval_minutes",
            "active_start_time", "active_end_time", "max_images", "updated_at",
        ]
        read_only_fields = ["farm", "updated_at"]

    def get_llm_api_key_configured(self, obj):
        return bool(obj.llm_api_key_encrypted)

    def get_vlm_api_key_configured(self, obj):
        return bool(obj.vlm_api_key_encrypted)

    def get_llm_api_key_mask(self, obj):
        return mask_api_key(obj.llm_api_key_encrypted)

    def get_vlm_api_key_mask(self, obj):
        return mask_api_key(obj.vlm_api_key_encrypted)

    def validate_timezone(self, value):
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise serializers.ValidationError("Use a valid IANA timezone name.") from exc
        return value

    def update(self, instance, validated_data):
        llm_key = validated_data.pop("llm_api_key", None)
        vlm_key = validated_data.pop("vlm_api_key", None)
        clear_llm = validated_data.pop("clear_llm_api_key", False)
        clear_vlm = validated_data.pop("clear_vlm_api_key", False)
        if clear_llm:
            instance.llm_api_key_encrypted = ""
        elif llm_key is not None:
            instance.llm_api_key_encrypted = encrypt_api_key(llm_key)
        if clear_vlm:
            instance.vlm_api_key_encrypted = ""
        elif vlm_key is not None:
            instance.vlm_api_key_encrypted = encrypt_api_key(vlm_key)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.full_clean()
        instance.save()
        return instance


class KasaActuatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = KasaActuator
        fields = ["id", "farm", "name", "target_device", "host", "child_index", "enabled"]
        read_only_fields = ["farm"]


class SafetyCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafetyCheck
        fields = ["id", "decision", "checked_at", "result", "explanation"]
        read_only_fields = fields


class FarmActionSerializer(serializers.ModelSerializer):
    actuator_name = serializers.CharField(source="actuator.name", read_only=True)

    class Meta:
        model = FarmAction
        fields = ["id", "decision", "actuator", "actuator_name", "requested_state", "previous_state", "confirmed_state", "attempted_at", "executed_at", "result", "explanation"]
        read_only_fields = fields


class AIDecisionSerializer(serializers.ModelSerializer):
    safety_check = serializers.SerializerMethodField()
    actions = FarmActionSerializer(many=True, read_only=True)

    def get_safety_check(self, obj):
        try:
            return SafetyCheckSerializer(obj.safetycheck).data
        except SafetyCheck.DoesNotExist:
            return None

    class Meta:
        model = AIDecision
        fields = ["id", "run", "device", "decision_type", "execution_type", "target_device", "device_state", "category", "recommendation", "explanation", "confidence_score", "output_used_fallback", "created_at", "safety_check", "actions"]
        read_only_fields = fields


class AIRecommendationRunSerializer(serializers.ModelSerializer):
    source_images = serializers.SerializerMethodField()
    recommendations = AIDecisionSerializer(many=True, read_only=True)

    def get_source_images(self, obj):
        request = self.context.get("request")
        result = []
        for image in obj.source_images.select_related("camera").all().order_by("camera_id"):
            url = image.path.url if image.path else None
            if request and url:
                url = request.build_absolute_uri(url)
            result.append({"id": image.id, "camera_id": image.camera_id, "camera_name": image.camera.name, "captured_at": image.captured_at, "url": url})
        return result

    class Meta:
        model = AIRecommendationRun
        fields = ["id", "farm", "trigger", "status", "scheduled_for", "input_mode", "provider_name", "model_name", "source_images", "image_observations", "fallback_used", "fallback_reason", "error", "created_at", "started_at", "completed_at", "recommendations"]
        read_only_fields = fields
