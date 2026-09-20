from django.urls import path
from rest_framework.routers import DefaultRouter

from telemetry import views


router = DefaultRouter()

router.register(r"farms", views.FarmViewSet)
router.register(r"farm-devices", views.FarmDeviceViewSet)
router.register(r"farm-levels", views.FarmLevelViewSet)
router.register(r"growing-areas", views.GrowingAreaViewSet)
router.register(r"plant-batches", views.PlantBatchViewSet)
router.register(r"batch-placements", views.BatchPlacementViewSet)

router.register(r"cameras", views.CameraViewSet)
router.register(r"camera-images", views.CameraImageViewSet)

router.register(r"sensors", views.SensorViewSet)
router.register(r"sensor-readings", views.SensorReadingViewSet)
router.register(r"actuator-state-observations", views.ActuatorStateObservationViewSet)
router.register(r"setpoint-observations", views.SetpointObservationViewSet)

router.register(r"nutrient-tanks", views.NutrientTankViewSet)
router.register(r"dosers", views.DoserViewSet)
router.register(r"safe-ranges", views.SafeRangeViewSet)

urlpatterns = [
    path("cameras/<int:camera_id>/official-image/", views.official_image, name="official-image"),
    path("cameras/<int:camera_id>/latest-image/", views.latest_image, name="latest-camera-image"),
]
