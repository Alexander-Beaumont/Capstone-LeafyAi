from django.urls import include, path
from rest_framework.routers import DefaultRouter

from telemetry import views


router = DefaultRouter()

router.register(r'farms', views.FarmViewSet)
router.register(r'farm-devices', views.FarmDeviceViewSet)
router.register(r'farm-levels', views.FarmLevelViewSet)
router.register(r'growing-areas', views.GrowingAreaViewSet)

router.register(r'plant-batches', views.PlantBatchViewSet)
router.register(r'batch-placements', views.BatchPlacementViewSet)

router.register(r'cameras', views.CameraViewSet)
router.register(r'sensors', views.SensorViewSet)
router.register(r'sensor-readings', views.SensorReadingViewSet)

router.register(r'nutrient-tanks', views.NutrientTankViewSet)
router.register(r'dosers', views.DoserViewSet)
router.register(r'safe-ranges', views.SafeRangeViewSet)