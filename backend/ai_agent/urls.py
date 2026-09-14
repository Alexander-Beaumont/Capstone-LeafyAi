from django.urls import path
from rest_framework.routers import DefaultRouter

from ai_agent import views


router = DefaultRouter()

router.register(r'ai-decisions', views.AIDecisionViewSet)
router.register(r'actions', views.FarmActionViewSet)
router.register(r'safety-checks', views.SafetyCheckViewSet)


urlpatterns = [
    path(
        "ai-agent/recommend/",
        views.recommend,
        name="ai-recommend",
    ),
]
