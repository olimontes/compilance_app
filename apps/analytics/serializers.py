from rest_framework import serializers

from apps.common.tenancy import user_has_active_membership
from apps.organizations.models import Organization

from .models import DataQualityCheck, IngestionRun, MetricDefinition, MetricSnapshot


class MetricDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetricDefinition
        fields = (
            "uuid",
            "key",
            "name",
            "description",
            "value_type",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("uuid", "created_at", "updated_at")


class MetricSnapshotSerializer(serializers.ModelSerializer):
    organization = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Organization.objects.all(),
    )
    metric_definition = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=MetricDefinition.objects.all(),
    )

    class Meta:
        model = MetricSnapshot
        fields = (
            "uuid",
            "organization",
            "metric_definition",
            "metric_value",
            "dimensions",
            "period_start",
            "period_end",
            "computed_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("uuid", "created_at", "updated_at")

    def validate_organization(self, organization):
        user = self.context["request"].user
        if user_has_active_membership(user, organization):
            return organization
        raise serializers.ValidationError("You are not a member of this organization.")


class DataQualityCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataQualityCheck
        fields = (
            "uuid",
            "check_key",
            "target_table",
            "status",
            "result",
            "executed_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("uuid", "created_at", "updated_at")


class IngestionRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngestionRun
        fields = (
            "uuid",
            "source_name",
            "status",
            "started_at",
            "finished_at",
            "rows_read",
            "rows_written",
            "error_message",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("uuid", "created_at", "updated_at")
