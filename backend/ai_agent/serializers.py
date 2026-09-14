from rest_framework import serializers

from ai_agent.models import (
    AIDecision,
    SafetyCheck,
    FarmAction,
)


class AIDecisionSerializer(serializers.ModelSerializer):
    safety_check = serializers.SerializerMethodField()
    notification_status = serializers.SerializerMethodField()

    def get_safety_check(self, obj):
        try:
            safety_check = obj.safetycheck
        except SafetyCheck.DoesNotExist:
            return None
        return SafetyCheckSerializer(safety_check).data

    def get_notification_status(self, obj):
        try:
            return "ready" if obj.safetycheck.result == "passed" else "blocked"
        except SafetyCheck.DoesNotExist:
            return "blocked"

    class Meta:
        model = AIDecision
        fields = [
            'id',
            'device',
            'input_mode',
            'model_name',
            'source_image',
            'source_analysis',
            'used_visual_input',
            'visual_status',
            'visual_reason',
            'fallback_used',
            'fallback_reason',
            'output_used_fallback',
            'decision_type',
            'execution_type',
            'target_device',
            'device_state',
            'category',
            'recommendation',
            'explanation',
            'confidence_score',
            'created_at',
            'safety_check',
            'notification_status',
        ]
        read_only_fields = fields

class SafetyCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafetyCheck
        fields = [
            'id',
            'decision',
            'checked_at',
            'result',
            'explanation',
        ]

        read_only_fields = fields


class FarmActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmAction
        fields = [
            'id',
            'decision',
            'executed_at',
            'result',
            'explanation',
        ]
        read_only_fields = fields
