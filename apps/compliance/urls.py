from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ControlViewSet, RiskControlViewSet, RiskViewSet

router = DefaultRouter()
router.register("controls", ControlViewSet, basename="control")
router.register("risks", RiskViewSet, basename="risk")
router.register("risk-controls", RiskControlViewSet, basename="risk-control")

urlpatterns = [
    path("", include(router.urls)),
]

