from django.urls import include, path
from rest_framework.routers import DefaultRouter

from ai_agent.views import AIDecisionViewSet
from telemetry.views import FarmViewSet, SensorViewSet


router = DefaultRouter()

# Telemetry
router.register(r"farms", FarmViewSet)
router.register(r"sensors", SensorViewSet)

# AI Agent
router.register(r"ai-decisions", AIDecisionViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
