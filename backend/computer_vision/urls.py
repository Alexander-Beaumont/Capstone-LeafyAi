from rest_framework.routers import DefaultRouter
from computer_vision import views

router = DefaultRouter()

router.register(r'image-analyses',views.ImageAnalysisViewSet)

router.register(r'plant-vision-measurements',views.PlantVisionMeasurementViewSet)