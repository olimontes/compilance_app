from rest_framework import viewsets

from apps.audit.services import log_create_event
from apps.common.tenancy import OrganizationScopedQuerySetMixin

from .models import Control, Risk, RiskControl
from .serializers import ControlSerializer, RiskControlSerializer, RiskSerializer


class ControlViewSet(OrganizationScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = ControlSerializer
    lookup_field = "uuid"
    queryset = Control.objects.none()

    def get_queryset(self):
        queryset = Control.objects.filter(organization_id__in=self.user_organization_ids())
        status = self.request.query_params.get("status")
        domain = self.request.query_params.get("domain")
        if status:
            queryset = queryset.filter(status=status)
        if domain:
            queryset = queryset.filter(domain=domain)
        return queryset

    def perform_create(self, serializer):
        control = serializer.save()
        log_create_event(
            actor_user=self.request.user,
            organization=control.organization,
            instance=control,
            event_type="control.created",
        )


class RiskViewSet(OrganizationScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = RiskSerializer
    lookup_field = "uuid"
    queryset = Risk.objects.none()

    def get_queryset(self):
        queryset = Risk.objects.filter(organization_id__in=self.user_organization_ids())
        status = self.request.query_params.get("status")
        severity = self.request.query_params.get("severity")
        if status:
            queryset = queryset.filter(status=status)
        if severity:
            queryset = queryset.filter(severity=severity)
        return queryset

    def perform_create(self, serializer):
        risk = serializer.save()
        log_create_event(
            actor_user=self.request.user,
            organization=risk.organization,
            instance=risk,
            event_type="risk.created",
        )


class RiskControlViewSet(OrganizationScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = RiskControlSerializer
    queryset = RiskControl.objects.none()

    def get_queryset(self):
        return RiskControl.objects.filter(risk__organization_id__in=self.user_organization_ids())
