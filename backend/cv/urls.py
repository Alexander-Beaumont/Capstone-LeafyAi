from rest_framework.routers import DefaultRouter
from cv import views
from django.urls import path

router = DefaultRouter()

router.register(r'image-analyses',views.ImageAnalysisViewSet)


urlpatterns = [
    path('cameras/<int:camera_id>/official-image/', views.official_image, name='official-image'),
    path('cv/cameras/<int:camera_id>/latest-image/', views.latest_image, name='cv-latest-image'),
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
