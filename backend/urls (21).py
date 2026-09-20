from django.urls import path
from . import views
urlpatterns = [
    path("devices/", views.devices, name="powerboard-devices"),
    path("devices/<int:device_id>/state/", views.device_state, name="powerboard-device-state"),
]
