from django.urls import path

from camera_capture import views


urlpatterns = [
    path("cameras/", views.cameras, name="camera-list"),
    path("cameras/<int:camera_id>/", views.camera_detail, name="camera-detail"),
    path(
        "cameras/<int:camera_id>/latest-image/",
        views.latest_image,
        name="camera-latest-image",
    ),
    path("camera-images/", views.camera_images, name="cameraimage-list"),
    path(
        "camera-images/<int:image_id>/",
        views.camera_image_detail,
        name="cameraimage-detail",
    ),
]
