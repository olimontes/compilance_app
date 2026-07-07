from rest_framework import viewsets

from apps.organizations.models import Membership, Organization

from .models import DataQualityCheck, IngestionRun, MetricDefinition, MetricSnapshot
from .serializers import (
    DataQualityCheckSerializer,
    IngestionRunSerializer,
    MetricDefinitionSerializer,
    MetricSnapshotSerializer,
)


class OrganizationScopedQuerySetMixin:
    def user_organization_ids(self):
        user = self.request.user
        if user.is_superuser:
            return Organization.objects.values_list("id", flat=True)
        return Membership.objects.filter(
            user=user,
            status=Membership.Status.ACTIVE,
        ).values_list("organization_id", flat=True)


class MetricDefinitionViewSet(viewsets.ModelViewSet):
    serializer_class = MetricDefinitionSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        queryset = MetricDefinition.objects.all()
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        return queryset


class MetricSnapshotViewSet(OrganizationScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = MetricSnapshotSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        queryset = MetricSnapshot.objects.filter(organization_id__in=self.user_organization_ids())
        metric_key = self.request.query_params.get("metric_key")
        if metric_key:
            queryset = queryset.filter(metric_definition__key=metric_key)
        return queryset


class DataQualityCheckViewSet(viewsets.ModelViewSet):
    serializer_class = DataQualityCheckSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        queryset = DataQualityCheck.objects.all()
        status = self.request.query_params.get("status")
        target_table = self.request.query_params.get("target_table")
        if status:
            queryset = queryset.filter(status=status)
        if target_table:
            queryset = queryset.filter(target_table=target_table)
        return queryset


class IngestionRunViewSet(viewsets.ModelViewSet):
    serializer_class = IngestionRunSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        queryset = IngestionRun.objects.all()
        status = self.request.query_params.get("status")
        source_name = self.request.query_params.get("source_name")
        if status:
            queryset = queryset.filter(status=status)
        if source_name:
            queryset = queryset.filter(source_name=source_name)
        return queryset

