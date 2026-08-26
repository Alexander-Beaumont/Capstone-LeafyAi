from django.urls import path

from growth import views


urlpatterns = [
    path("growing-areas", views.growing_areas, name="growing-areas"),
    path("growing-areas/", views.growing_areas, name="growing-areas-slash"),
    path("batches", views.batches, name="batches"),
    path("batches/", views.batches, name="batches-slash"),
    path("move-batch", views.move_batch, name="move-batch"),
    path("move-batch/", views.move_batch, name="move-batch-slash"),
    path("create-growing-area", views.create_growing_area, name="create-growing-area"),
    path("create-growing-area/", views.create_growing_area, name="create-growing-area-slash"),
    path("update-growing-area", views.update_growing_area, name="update-growing-area"),
    path("update-growing-area/", views.update_growing_area, name="update-growing-area-slash"),
    path("update-batch", views.update_batch, name="update-batch"),
    path("update-batch/", views.update_batch, name="update-batch-slash"),
    path("create-batch", views.create_batch, name="create-batch"),
    path("create-batch/", views.create_batch, name="create-batch-slash"),
]
