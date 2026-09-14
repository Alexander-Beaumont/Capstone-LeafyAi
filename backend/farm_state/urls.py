from django.urls import path

from farm_state import views

urlpatterns = [
    path(
        "farm-state/<int:farm_id>/",
        views.farm_state,
        name="farm-state",
    ),
]