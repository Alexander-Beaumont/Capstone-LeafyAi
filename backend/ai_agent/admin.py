from django.contrib import admin

from ai_agent.models import AIDecision, FarmAction, SafetyCheck


admin.site.register(AIDecision)
admin.site.register(SafetyCheck)
admin.site.register(FarmAction)
