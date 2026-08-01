from django.urls import path, include
from rest_framework.routers import DefaultRouter

from telemetry.views import *

from ai_agent.views import *


router = DefaultRouter()

# Telemetry
router.register(r'farms', FarmViewSet)
router.register(r'sensors', SensorViewSet)
router.register(r'cameras', CameraViewSet)

# AI Agent
router.register(r'ai-decisions', AIDecisionViewSet)


urlpatterns = [
    path('', include(router.urls)),
]