from drf_spectacular.utils import extend_schema, inline_serializer
from django.db.models import Count
from rest_framework import decorators, response, serializers, viewsets

from apps.ai_assets.models import AiUseCase, RiskLevel
from apps.assessments.models import Assessment
from apps.common.tenancy import OrganizationScopedQuerySetMixin, active_organization_ids_for_user
from apps.compliance.models import Control, Risk
from apps.evidence.models import Evidence
from apps.organizations.models import Organization

from .models import DataQualityCheck, IngestionRun, MetricDefinition, MetricSnapshot
from .serializers import (
    DataQualityCheckSerializer,
    IngestionRunSerializer,
    MetricDefinitionSerializer,
    MetricSnapshotSerializer,
)


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
    queryset = MetricSnapshot.objects.none()

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


def _choice_counts(queryset, field_name, choices):
    counts = {value: 0 for value, _label in choices}
    for item in queryset.values(field_name).annotate(count=Count("id")):
        counts[item[field_name]] = item["count"]
    return counts


@extend_schema(
    responses=inline_serializer(
        name="MetricsOverviewResponse",
        fields={
            "organizations": serializers.IntegerField(),
            "ai_use_cases": serializers.IntegerField(),
            "controls": serializers.IntegerField(),
            "evidence": serializers.IntegerField(),
            "risks_by_severity": serializers.DictField(child=serializers.IntegerField()),
            "risks_by_status": serializers.DictField(child=serializers.IntegerField()),
            "assessments_by_status": serializers.DictField(child=serializers.IntegerField()),
        },
    )
)
@decorators.api_view(["GET"])
def metrics_overview(request):
    organization_ids = active_organization_ids_for_user(request.user)

    risks = Risk.objects.filter(organization_id__in=organization_ids)
    assessments = Assessment.objects.filter(organization_id__in=organization_ids)

    payload = {
        "organizations": Organization.objects.filter(id__in=organization_ids).count(),
        "ai_use_cases": AiUseCase.objects.filter(organization_id__in=organization_ids).count(),
        "controls": Control.objects.filter(organization_id__in=organization_ids).count(),
        "evidence": Evidence.objects.filter(organization_id__in=organization_ids).count(),
        "risks_by_severity": _choice_counts(risks, "severity", RiskLevel.choices),
        "risks_by_status": _choice_counts(risks, "status", Risk.Status.choices),
        "assessments_by_status": _choice_counts(assessments, "status", Assessment.Status.choices),
    }
    return response.Response(payload)
