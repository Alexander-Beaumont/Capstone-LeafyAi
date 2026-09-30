from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView

from accounts.views import SafeTokenRefreshView
from ai_agent.urls import router as ai_agent_router
from telemetry.urls import router as telemetry_router


router = DefaultRouter()
router.registry.extend(telemetry_router.registry)
router.registry.extend(ai_agent_router.registry)

urlpatterns = [
    path("api/", include(router.urls)),
    path("api/auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", SafeTokenRefreshView.as_view(), name="token_refresh"),
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("farm_state.urls")),
    path("api/", include("sensor_ingest.urls")),
    path("api/", include("telemetry.operator_urls")),
    path("api/", include("growth.urls")),
    path("api/", include("ai_agent.urls")),
    path("api/", include("powerboard_control.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
