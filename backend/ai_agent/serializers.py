from rest_framework import serializers

from ai_agent.models import (
    AIDecision,
    SafetyCheck,
    HumanApproval,
    FarmAction,
)


class AIDecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIDecision
<<<<<<< HEAD
        fields = ['id', 'plant_batch' 'decision_type', 'recommendation', 'explanation', 'confidence_score', 'created_at']
=======
        fields = [
            'id',
            'device',
            'decision_type',
            'execution_type',
            'target_device',
            'device_state',
            'category',
            'recommendation',
            'explanation',
            'confidence_score',
            'created_at',
        ]

        read_only_fields = [
            'created_at',
        ]

>>>>>>> f504721e64d9aad837c24599c8aed59986118f4a

class SafetyCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafetyCheck
<<<<<<< HEAD
        fields = ['ai_decision', 'checked_at', 'result', 'explanation']
=======
        fields = [
            'id',
            'decision',
            'checked_at',
            'result',
            'explanation',
        ]

        read_only_fields = [
            'checked_at',
        ]

>>>>>>> f504721e64d9aad837c24599c8aed59986118f4a

class HumanApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = HumanApproval
        fields = [
            'id',
            'decision',
            'result',
            'comment',
        ]


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
