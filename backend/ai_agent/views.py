from rest_framework import viewsets

from ai_agent.models import *
from ai_agent.serializers import *


class AIDecisionViewSet(viewsets.ModelViewSet):
    queryset = AIDecision.objects.all()
    serializer_class = AIDecisionSerializer


class FarmActionViewSet(viewsets.ModelViewSet):
    queryset = FarmAction.objects.all()
    serializer_class = FarmActionSerializer


class HumanApprovalViewSet(viewsets.ModelViewSet):
    queryset = HumanApproval.objects.all()
    serializer_class = HumanApprovalSerializer


class SafetyCheckViewSet(viewsets.ModelViewSet):
    queryset = SafetyCheck.objects.all()
    serializer_class = SafetyCheckSerializer