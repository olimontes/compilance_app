from rest_framework import serializers

from apps.organizations.models import Membership, Organization, OrganizationUnit

from .models import AiTool, AiUseCase, AiVendor


class OrganizationScopedSerializerMixin:
    def validate_organization(self, organization):
        user = self.context["request"].user
        if user.is_superuser:
            return organization
        if organization.memberships.filter(user=user, status=Membership.Status.ACTIVE).exists():
            return organization
        raise serializers.ValidationError("You are not a member of this organization.")


class AiVendorSerializer(OrganizationScopedSerializerMixin, serializers.ModelSerializer):
    organization = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Organization.objects.all(),
    )

    class Meta:
        model = AiVendor
        fields = ("uuid", "organization", "name", "website", "risk_level", "created_at", "updated_at")
        read_only_fields = ("uuid", "created_at", "updated_at")


class AiToolSerializer(OrganizationScopedSerializerMixin, serializers.ModelSerializer):
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
        organization = attrs.get("organization") or getattr(self.instance, "organization", None)
        vendor = attrs.get("vendor")
        if vendor and organization and vendor.organization_id != organization.id:
            raise serializers.ValidationError({"vendor": "Vendor must belong to the same organization."})
        return attrs


class AiUseCaseSerializer(OrganizationScopedSerializerMixin, serializers.ModelSerializer):
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
        organization = attrs.get("organization") or getattr(self.instance, "organization", None)
        ai_tool = attrs.get("ai_tool")
        organization_unit = attrs.get("organization_unit")
        if ai_tool and organization and ai_tool.organization_id != organization.id:
            raise serializers.ValidationError({"ai_tool": "AI tool must belong to the same organization."})
        if organization_unit and organization and organization_unit.organization_id != organization.id:
            raise serializers.ValidationError(
                {"organization_unit": "Organization unit must belong to the same organization."}
            )
        return attrs

