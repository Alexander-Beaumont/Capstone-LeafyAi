from django.urls import path

from . import views


urlpatterns = [
    path(
        "farms/<int:farm_id>/powerboard-config/",
        views.farm_powerboard_config,
        name="farm-powerboard-config",
    ),
    path("devices/", views.devices, name="powerboard-devices"),
    path(
        "devices/<int:device_id>/state/",
        views.device_state,
        name="powerboard-device-state",
    ),
]
