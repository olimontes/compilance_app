from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AiAssetOwnerViewSet,
    AiModelViewSet,
    AiToolViewSet,
    AiUseCaseViewSet,
    AiVendorViewSet,
    DataSourceViewSet,
)

router = DefaultRouter()
router.register("ai-vendors", AiVendorViewSet, basename="ai-vendor")
router.register("ai-tools", AiToolViewSet, basename="ai-tool")
router.register("ai-models", AiModelViewSet, basename="ai-model")
router.register("ai-use-cases", AiUseCaseViewSet, basename="ai-use-case")
router.register("data-sources", DataSourceViewSet, basename="data-source")
router.register("ai-asset-owners", AiAssetOwnerViewSet, basename="ai-asset-owner")

urlpatterns = [
    path("", include(router.urls)),
]
