from rest_framework import viewsets

from apps.organizations.models import Membership, Organization

from .models import Control, Risk, RiskControl
from .serializers import ControlSerializer, RiskControlSerializer, RiskSerializer


class OrganizationScopedQuerySetMixin:
    def user_organization_ids(self):
        user = self.request.user
        if user.is_superuser:
            return Organization.objects.values_list("id", flat=True)
        return Membership.objects.filter(
            user=user,
            status=Membership.Status.ACTIVE,
        ).values_list("organization_id", flat=True)


class ControlViewSet(OrganizationScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = ControlSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        queryset = Control.objects.filter(organization_id__in=self.user_organization_ids())
        status = self.request.query_params.get("status")
        domain = self.request.query_params.get("domain")
        if status:
            queryset = queryset.filter(status=status)
        if domain:
            queryset = queryset.filter(domain=domain)
        return queryset


class RiskViewSet(OrganizationScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = RiskSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        queryset = Risk.objects.filter(organization_id__in=self.user_organization_ids())
        status = self.request.query_params.get("status")
        severity = self.request.query_params.get("severity")
        if status:
            queryset = queryset.filter(status=status)
        if severity:
            queryset = queryset.filter(severity=severity)
        return queryset


class RiskControlViewSet(OrganizationScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = RiskControlSerializer

    def get_queryset(self):
        return RiskControl.objects.filter(risk__organization_id__in=self.user_organization_ids())

