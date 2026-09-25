from django.urls import path
from rest_framework.routers import DefaultRouter

from ai_agent import views

router = DefaultRouter()
router.register(r"ai-decisions", views.AIDecisionViewSet)
router.register(r"actions", views.FarmActionViewSet)
router.register(r"safety-checks", views.SafetyCheckViewSet)

urlpatterns = [
    path("ai-agent/recommend/", views.recommend, name="ai-recommend"),
    path("ai-agent/farms/<int:farm_id>/settings/", views.farm_settings, name="ai-farm-settings"),
    path("ai-agent/farms/<int:farm_id>/providers/test/", views.test_provider, name="ai-provider-test"),
    path("ai-agent/farms/<int:farm_id>/recommendations/generate/", views.generate_for_farm, name="ai-generate"),
    path("ai-agent/farms/<int:farm_id>/recommendations/latest/", views.latest_recommendations, name="ai-latest"),
    path("ai-agent/farms/<int:farm_id>/recommendations/recent/", views.recent_recommendations, name="ai-recent"),
    path("ai-agent/farms/<int:farm_id>/recommendations/history/", views.recommendation_history, name="ai-history"),
    path("ai-agent/farms/<int:farm_id>/recommendations/<int:run_id>/", views.recommendation_detail, name="ai-run-detail"),
]
