from rest_framework import viewsets

from apps.common.tenancy import OrganizationScopedQuerySetMixin

from .models import AuditEvent, DataChangeLog
from .serializers import AuditEventSerializer, DataChangeLogSerializer


class AuditEventViewSet(OrganizationScopedQuerySetMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditEventSerializer
    lookup_field = "uuid"
    queryset = AuditEvent.objects.none()

    def get_queryset(self):
        queryset = AuditEvent.objects.select_related("organization", "actor_user")
        if not self.request.user.is_superuser:
            queryset = queryset.filter(organization_id__in=self.user_organization_ids())

        event_type = self.request.query_params.get("event_type")
        entity_type = self.request.query_params.get("entity_type")
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)
        return queryset


class DataChangeLogViewSet(OrganizationScopedQuerySetMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = DataChangeLogSerializer
    lookup_field = "uuid"
    queryset = DataChangeLog.objects.none()

    def get_queryset(self):
        queryset = DataChangeLog.objects.select_related("audit_event", "audit_event__organization")
        if not self.request.user.is_superuser:
            queryset = queryset.filter(audit_event__organization_id__in=self.user_organization_ids())

        action = self.request.query_params.get("action")
        entity_type = self.request.query_params.get("entity_type")
        if action:
            queryset = queryset.filter(action=action)
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)
        return queryset
