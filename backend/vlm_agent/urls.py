from django.urls import path
from rest_framework.routers import DefaultRouter

from vlm_agent import views


router = DefaultRouter()
router.register(r"vlm-decisions", views.VLMDecisionViewSet)
router.register(r"vlm-actions", views.VLMFarmActionViewSet)
router.register(r"vlm-human-approvals", views.VLMHumanApprovalViewSet)
router.register(r"vlm-safety-checks", views.VLMSafetyCheckViewSet)


urlpatterns = [
    path("vlm-agent/recommend/", views.recommend, name="vlm-recommend"),
]
