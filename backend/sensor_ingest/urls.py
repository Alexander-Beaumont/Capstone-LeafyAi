from django.urls import include, path
from rest_framework.routers import DefaultRouter

from sensor_ingest import views


router = DefaultRouter()
router.register(
    r"sensor-ingest/sources",
    views.IngestionSourceStateViewSet,
    basename="sensor-ingest-source",
)
router.register(
    r"sensor-ingest/records",
    views.IngestionRecordViewSet,
    basename="sensor-ingest-record",
)

urlpatterns = [
    path(
        "sensor-ingest/health/",
        views.sensor_ingest_health,
        name="sensor-ingest-health",
    ),
    path("", include(router.urls)),
]
