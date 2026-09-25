from django.urls import path

from telemetry import operator_views as views


urlpatterns = [
    path("farms/<int:farm_id>/dashboard/", views.dashboard, name="farm-dashboard"),
    path("farms/<int:farm_id>/sensor-readings/", views.sensor_readings, name="farm-sensor-readings"),
    path("farms/<int:farm_id>/sensor-history/", views.sensor_history, name="farm-sensor-history"),
    path("farms/<int:farm_id>/cameras/", views.cameras, name="farm-cameras"),
    path("farms/<int:farm_id>/cameras/<int:camera_id>/", views.camera_detail, name="farm-camera-detail"),
    path("farms/<int:farm_id>/cameras/<int:camera_id>/capture/", views.capture_camera, name="farm-camera-capture"),
    path("farms/<int:farm_id>/camera-images/", views.camera_images, name="farm-camera-images"),
]
