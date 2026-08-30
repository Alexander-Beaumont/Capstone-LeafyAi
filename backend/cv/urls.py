from django.urls import path

from cv import views


urlpatterns = [
    # LeafyCV sends analysis results for an existing CameraImage
    path(
        "cv/ingest/",
        views.ingest_cv_result,
        name="cv-ingest"
    ),

    # Latest official image captured for a camera
    path(
        "cv/cameras/<int:camera_id>/latest-image/",
        views.latest_image,
        name="cv-latest-image"
    ),

    # Latest CV analysis for a camera
    #
    # Also supports:
    # ?valid=true
    path(
        "cv/cameras/<int:camera_id>/latest-analysis/",
        views.latest_analysis,
        name="cv-latest-analysis"
    ),
]