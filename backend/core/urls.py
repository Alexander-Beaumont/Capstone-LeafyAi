from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from telemetry.urls import router as telemetry_router
from ai_agent.urls import router as ai_agent_router
from vlm_agent.urls import router as vlm_agent_router
from cv.urls import router as cv_router


def health(_request):
    # Unauthenticated container/readiness check. No farm data is exposed.
    return JsonResponse({"status": "ok"})


router = DefaultRouter()
router.registry.extend(telemetry_router.registry)
# Keep legacy model routes available for compatibility, but the no-AI MVP UI
# does not use them.
router.registry.extend(ai_agent_router.registry)
router.registry.extend(vlm_agent_router.registry)
router.registry.extend(cv_router.registry)

urlpatterns = [
    path("health/", health, name="health"),
    path("api/", include(router.urls)),
    path("api/auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/", include("accounts.urls")),
    # Function endpoints that are not router ViewSets.
    path("api/", include("cv.urls")),
    path("api/", include("farm_state.urls")),
    path("api/", include("growth.urls")),
    path("api/", include("ai_agent.urls")),
    path("api/", include("vlm_agent.urls")),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
