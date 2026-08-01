from django.urls import include, path
from rest_framework.routers import DefaultRouter

from ai_agent import views

router = DefaultRouter()
router.register(r'ai-decisions', views.AIDecisionViewSet)
router.register(r'actions', views.ActionViewSet)
router.register(r'human-approvals', views.HumanApprovalViewSet)
router.register(r'safety-checks', views.SafetyCheckViewSet)

#urlpatterns = [
#    path('', include(router.urls)),
#]
