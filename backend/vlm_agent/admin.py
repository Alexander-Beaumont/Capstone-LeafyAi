from django.contrib import admin

from vlm_agent.models import (
    VLMDecision,
    VLMFarmAction,
    VLMHumanApproval,
    VLMSafetyCheck,
)


admin.site.register(VLMDecision)
admin.site.register(VLMSafetyCheck)
admin.site.register(VLMHumanApproval)
admin.site.register(VLMFarmAction)
