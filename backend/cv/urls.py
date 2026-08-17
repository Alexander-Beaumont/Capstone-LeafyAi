from rest_framework.routers import DefaultRouter
from cv import views
from django.urls import path

router = DefaultRouter()

router.register(r'image-analyses',views.ImageAnalysisViewSet)

router.register(r'plant-vision-measurements',views.PlantVisionMeasurementViewSet)


urlpatterns = [
    path(
        'cv/ingest/',
        views.ingest_cv_result,
        name='cv-ingest'
    ),
    path(
        "cv/cameras/<int:camera_id>/latest-analysis/",
        views.latest_analysis,
        name="cv-latest-analysis"
    ),

]

