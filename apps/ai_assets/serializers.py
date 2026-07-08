from rest_framework import serializers

from apps.common.tenancy import OrganizationMembershipValidatorMixin, serializer_field_value
from apps.organizations.models import Membership, Organization, OrganizationUnit

from .models import AiAssetOwner, AiModel, AiTool, AiUseCase, AiVendor, DataSource


class AiVendorSerializer(OrganizationMembershipValidatorMixin, serializers.ModelSerializer):
    organization = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Organization.objects.all(),
    )

    class Meta:
        model = AiVendor
        fields = ("uuid", "organization", "name", "website", "risk_level", "created_at", "updated_at")
        read_only_fields = ("uuid", "created_at", "updated_at")


class AiToolSerializer(OrganizationMembershipValidatorMixin, serializers.ModelSerializer):
    organization = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Organization.objects.all(),
    )
    vendor = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=AiVendor.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = AiTool
        fields = (
            "uuid",
            "organization",
            "vendor",
            "name",
            "category",
            "description",
            "status",
            "handles_personal_data",
            "handles_sensitive_data",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("uuid", "created_at", "updated_at")

    def validate(self, attrs):
        organization = serializer_field_value(self, attrs, "organization")
        vendor = serializer_field_value(self, attrs, "vendor")
        if vendor and organization and vendor.organization_id != organization.id:
            raise serializers.ValidationError({"vendor": "Vendor must belong to the same organization."})
        return attrs


class AiModelSerializer(OrganizationMembershipValidatorMixin, serializers.ModelSerializer):
    organization = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Organization.objects.all(),
    )
    ai_tool = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=AiTool.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = AiModel
        fields = (
            "uuid",
            "organization",
            "ai_tool",
            "name",
            "provider_model_id",
            "model_type",
            "status",
            "risk_level",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("uuid", "created_at", "updated_at")

    def validate(self, attrs):
        organization = serializer_field_value(self, attrs, "organization")
        ai_tool = serializer_field_value(self, attrs, "ai_tool")
        if ai_tool and organization and ai_tool.organization_id != organization.id:
            raise serializers.ValidationError({"ai_tool": "AI tool must belong to the same organization."})
        return attrs


class AiUseCaseSerializer(OrganizationMembershipValidatorMixin, serializers.ModelSerializer):
    organization = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Organization.objects.all(),
    )
    ai_tool = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=AiTool.objects.all(),
        required=False,
        allow_null=True,
    )
    organization_unit = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=OrganizationUnit.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = AiUseCase
        fields = (
            "uuid",
            "organization",
            "ai_tool",
            "organization_unit",
            "name",
            "business_area",
            "purpose",
            "data_classification",
            "risk_level",
            "lifecycle_stage",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("uuid", "created_at", "updated_at")

    def validate(self, attrs):
        organization = serializer_field_value(self, attrs, "organization")
        ai_tool = serializer_field_value(self, attrs, "ai_tool")
        organization_unit = serializer_field_value(self, attrs, "organization_unit")
        if ai_tool and organization and ai_tool.organization_id != organization.id:
            raise serializers.ValidationError({"ai_tool": "AI tool must belong to the same organization."})
        if organization_unit and organization and organization_unit.organization_id != organization.id:
            raise serializers.ValidationError(
                {"organization_unit": "Organization unit must belong to the same organization."}
            )
        return attrs


class DataSourceSerializer(OrganizationMembershipValidatorMixin, serializers.ModelSerializer):
    organization = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Organization.objects.all(),
    )
    ai_use_case = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=AiUseCase.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = DataSource
        fields = (
            "uuid",
            "organization",
            "ai_use_case",
            "name",
            "source_type",
            "description",
            "data_classification",
            "contains_personal_data",
            "contains_sensitive_data",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("uuid", "created_at", "updated_at")

    def validate(self, attrs):
        organization = serializer_field_value(self, attrs, "organization")
        ai_use_case = serializer_field_value(self, attrs, "ai_use_case")
        if ai_use_case and organization and ai_use_case.organization_id != organization.id:
            raise serializers.ValidationError({"ai_use_case": "AI use case must belong to the same organization."})
        return attrs


class AiAssetOwnerSerializer(OrganizationMembershipValidatorMixin, serializers.ModelSerializer):
    organization = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Organization.objects.all(),
    )
    ai_use_case = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=AiUseCase.objects.all(),
    )
    membership = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Membership.objects.all(),
    )

    class Meta:
        model = AiAssetOwner
        fields = (
            "uuid",
            "organization",
            "ai_use_case",
            "membership",
            "responsibility",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("uuid", "created_at", "updated_at")

    def validate(self, attrs):
        organization = serializer_field_value(self, attrs, "organization")
        ai_use_case = serializer_field_value(self, attrs, "ai_use_case")
        membership = serializer_field_value(self, attrs, "membership")
        errors = {}
        if ai_use_case and organization and ai_use_case.organization_id != organization.id:
            errors["ai_use_case"] = "AI use case must belong to the same organization."
        if membership and organization and membership.organization_id != organization.id:
            errors["membership"] = "Membership must belong to the same organization."
        if errors:
            raise serializers.ValidationError(errors)
        return attrs
