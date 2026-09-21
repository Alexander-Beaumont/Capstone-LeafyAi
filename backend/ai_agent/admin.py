from django.contrib import admin

from ai_agent.models import AIConfiguration, AIDecision, AIRecommendationRun, FarmAction, SafetyCheck

admin.site.register([AIConfiguration, AIRecommendationRun, AIDecision, SafetyCheck, FarmAction])
