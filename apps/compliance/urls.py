from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ActionItemViewSet,
    ActionPlanViewSet,
    ControlViewSet,
    PolicyViewSet,
    RiskAssessmentViewSet,
    RiskControlViewSet,
    RiskViewSet,
)

router = DefaultRouter()
router.register("controls", ControlViewSet, basename="control")
router.register("risks", RiskViewSet, basename="risk")
router.register("risk-controls", RiskControlViewSet, basename="risk-control")
router.register("risk-assessments", RiskAssessmentViewSet, basename="risk-assessment")
router.register("policies", PolicyViewSet, basename="policy")
router.register("action-plans", ActionPlanViewSet, basename="action-plan")
router.register("action-items", ActionItemViewSet, basename="action-item")

urlpatterns = [
    path("", include(router.urls)),
]
