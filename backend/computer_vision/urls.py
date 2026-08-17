from rest_framework.routers import DefaultRouter
from computer_vision import views
from django.urls import path

router = DefaultRouter()

router.register(r'image-analyses',views.ImageAnalysisViewSet)

router.register(r'plant-vision-measurements',views.PlantVisionMeasurementViewSet)

from rest_framework.routers import DefaultRouter

from computer_vision import views


urlpatterns = [
    path(
        'cv/ingest/',
        views.ingest_cv_result,
        name='cv-ingest'
    ),
]