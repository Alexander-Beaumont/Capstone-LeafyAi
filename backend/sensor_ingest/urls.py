from django.urls import path

from sensor_ingest import views


urlpatterns = [
    path("farms/<int:farm_id>/sensor-ingest/", views.configuration_list, name="sensor-ingest-list"),
    path("farms/<int:farm_id>/sensor-ingest/<int:device_id>/", views.configuration_detail, name="sensor-ingest-detail"),
    path("farms/<int:farm_id>/sensor-ingest/<int:device_id>/test/", views.test_configuration, name="sensor-ingest-test"),
    path("farms/<int:farm_id>/sensor-ingest/<int:device_id>/collect/", views.collect_now, name="sensor-ingest-collect"),
]
