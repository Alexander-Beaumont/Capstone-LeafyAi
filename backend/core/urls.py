from django.urls import path, include
from django.contrib import admin
#from api_urls import *

from telemetry.urls import router as telemetryrouter
from ai_agent.urls import router as ai_agent_router 
from cv.urls import router as computer_vision_router
from rest_framework.routers import DefaultRouter 

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()

router.registry.extend(telemetryrouter.registry)
router.registry.extend(ai_agent_router.registry)
router.registry.extend(computer_vision_router.registry)


urlpatterns = [
    path('api/', include(router.urls)),
    path('api/auth/login/',TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path("api/", include("cv.urls")), #unsure
    path("api/", include("farm_state.urls")),
    path("api/", include("growth.urls")),
    path("api/", include("ai_agent.urls")),

]
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
