from django.urls import path, include
from django.contrib import admin
#from api_urls import *

from telemetry.urls import router as telemetryrouter
from ai_agent.urls import router as ai_agent_router 
from rest_framework.routers import DefaultRouter 

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = DefaultRouter()

router.registry.extend(telemetryrouter.registry)
router.registry.extend(ai_agent_router.registry)


urlpatterns = [
    path('api/', include(router.urls)),

    path('api/auth/login/',
         TokenObtainPairView.as_view(), 
         name='token_obtain_pair'),

    path('api/auth/refresh/', 
         TokenRefreshView.as_view(), 
         name='token_refresh'),
    path('admin/', admin.site.urls),

]