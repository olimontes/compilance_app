from rest_framework import viewsets

from apps.organizations.models import Membership, Organization

from .models import AiTool, AiUseCase, AiVendor
from .serializers import AiToolSerializer, AiUseCaseSerializer, AiVendorSerializer


class OrganizationScopedQuerySetMixin:
    def user_organization_ids(self):
        user = self.request.user
        if user.is_superuser:
            return Organization.objects.values_list("id", flat=True)
        return Membership.objects.filter(
            user=user,
            status=Membership.Status.ACTIVE,
        ).values_list("organization_id", flat=True)


class AiVendorViewSet(OrganizationScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = AiVendorSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        queryset = AiVendor.objects.filter(organization_id__in=self.user_organization_ids())
        risk_level = self.request.query_params.get("risk_level")
        if risk_level:
            queryset = queryset.filter(risk_level=risk_level)
        return queryset


class AiToolViewSet(OrganizationScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = AiToolSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        queryset = AiTool.objects.filter(organization_id__in=self.user_organization_ids())
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        return queryset


class AiUseCaseViewSet(OrganizationScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = AiUseCaseSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        queryset = AiUseCase.objects.filter(organization_id__in=self.user_organization_ids())
        risk_level = self.request.query_params.get("risk_level")
        lifecycle_stage = self.request.query_params.get("lifecycle_stage")
        if risk_level:
            queryset = queryset.filter(risk_level=risk_level)
        if lifecycle_stage:
            queryset = queryset.filter(lifecycle_stage=lifecycle_stage)
        return queryset

