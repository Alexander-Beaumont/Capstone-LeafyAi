from django.contrib import admin

from ai_agent.models import AIConfiguration, AIDecision, AIRecommendationRun, FarmAction, KasaActuator, SafetyCheck


admin.site.register(AIDecision)
admin.site.register(SafetyCheck)
admin.site.register(FarmAction)
admin.site.register(AIRecommendationRun)
admin.site.register(AIConfiguration)
admin.site.register(KasaActuator)
