from django.db import models
from rest_framework import serializers
from ai_agent.models import *

class AiDecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIDecision
        fields = ['id', 'decision_type', 'recommendation', 'explanation', 'confidence_score', 'created_at']


class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        fields = ['id', 'ai_decision', 'result', 'explanation', 'executed_at']

class HumanApprovalSerializer(serializers.ModelSerializer):
    class Meta:
        model = HumanApproval
        fields = ['AIDecision', 'result', 'comments', 'reviewed_at']

class SafetyCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = safetyCheck
        fields = ['AIDecision', 'checked_at', 'result', 'explanation']
