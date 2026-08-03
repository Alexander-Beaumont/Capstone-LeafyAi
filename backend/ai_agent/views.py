from rest_framework import viewsets
from ai_agent.models import *
from ai_agent.serializers import *


# Create your views here.
class AIDecisionViewSet(viewsets.ModelViewSet):
    queryset = AIDecision.objects.all()
    serializer_class = AiDecisionSerializer

class ActionViewSet(viewsets.ModelViewSet):
    queryset = FarmAction.objects.all()
    serializer_class = ActionSerializer

class HumanApprovalViewSet(viewsets.ModelViewSet):
    queryset = HumanApproval.objects.all()
    serializer_class = HumanApprovalSerializer

class SafetyCheckViewSet(viewsets.ModelViewSet):
    queryset = SafetyCheck.objects.all()
    serializer_class = SafetyCheckSerializer