from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AuditEventViewSet, DataChangeLogViewSet

router = DefaultRouter()
router.register("audit-events", AuditEventViewSet, basename="audit-event")
router.register("data-change-logs", DataChangeLogViewSet, basename="data-change-log")

urlpatterns = [
    path("", include(router.urls)),
]
