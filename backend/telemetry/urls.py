from django.urls import include, path
from rest_framework.routers import DefaultRouter

from telemetry import views

router = DefaultRouter()
router.register(r'farms', views.FarmViewSet)
router.register(r'farm-levels', views.FarmLevelViewSet)
router.register(r'plant-batches', views.PlantBatchViewSet)
router.register(r'cameras', views.CameraViewSet)
router.register(r'camera-images', views.CameraImageViewSet)
router.register(r'sensors', views.SensorViewSet)
router.register(r'sensor-readings', views.SensorReadingViewSet)



#urlpatterns = [
 #   path('', include(router.urls)),
#]
