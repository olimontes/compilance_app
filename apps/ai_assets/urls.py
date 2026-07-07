from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AiToolViewSet, AiUseCaseViewSet, AiVendorViewSet

router = DefaultRouter()
router.register("ai-vendors", AiVendorViewSet, basename="ai-vendor")
router.register("ai-tools", AiToolViewSet, basename="ai-tool")
router.register("ai-use-cases", AiUseCaseViewSet, basename="ai-use-case")

urlpatterns = [
    path("", include(router.urls)),
]

