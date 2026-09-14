from rest_framework import serializers

from vlm_agent.models import VLMDecision, VLMFarmAction, VLMHumanApproval, VLMSafetyCheck


class VLMDecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VLMDecision
        fields = [
            "id", "device", "source_image", "source_analysis", "used_visual_input",
            "visual_status", "visual_reason", "model_name", "decision_type",
            "execution_type", "target_device", "device_state", "category",
            "recommendation", "explanation", "confidence_score", "created_at",
        ]
        read_only_fields = ["created_at"]


class VLMSafetyCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = VLMSafetyCheck
        fields = ["id", "decision", "checked_at", "result", "explanation"]
        read_only_fields = ["checked_at"]


class VLMHumanApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = VLMHumanApproval
        fields = ["id", "decision", "result", "comment"]


class VLMFarmActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VLMFarmAction
        fields = ["id", "decision", "executed_at", "result", "explanation"]
