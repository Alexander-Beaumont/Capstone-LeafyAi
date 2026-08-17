from django.db import models
from rest_framework import serializers
from ai_agent.models import *

class AiDecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIDecision
        fields = ['id', 'plant_batch' 'decision_type', 'recommendation', 'explanation', 'confidence_score', 'created_at']

class SafetyCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafetyCheck
        fields = ['ai_decision', 'checked_at', 'result', 'explanation']

class HumanApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = HumanApproval
        fields = ['ai_decision', 'result', 'comment', 'reviewed_at']

class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmAction
        fields = ['id', 'ai_decision', 'result', 'explanation', 'executed_at']
