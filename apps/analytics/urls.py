from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    DataQualityCheckViewSet,
    IngestionRunViewSet,
    MetricDefinitionViewSet,
    MetricSnapshotViewSet,
    metrics_overview,
)

router = DefaultRouter()
router.register("metric-definitions", MetricDefinitionViewSet, basename="metric-definition")
router.register("metric-snapshots", MetricSnapshotViewSet, basename="metric-snapshot")
router.register("data-quality-checks", DataQualityCheckViewSet, basename="data-quality-check")
router.register("ingestion-runs", IngestionRunViewSet, basename="ingestion-run")

urlpatterns = [
    path("metrics/overview/", metrics_overview, name="metrics-overview"),
    path("", include(router.urls)),
]
