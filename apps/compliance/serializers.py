from rest_framework import serializers

from apps.ai_assets.models import AiUseCase
from apps.organizations.models import Membership, Organization

from .models import Control, Risk, RiskControl


class OrganizationMembershipValidatorMixin:
    def validate_organization(self, organization):
        user = self.context["request"].user
        if user.is_superuser:
            return organization
        if organization.memberships.filter(user=user, status=Membership.Status.ACTIVE).exists():
            return organization
        raise serializers.ValidationError("You are not a member of this organization.")


class ControlSerializer(OrganizationMembershipValidatorMixin, serializers.ModelSerializer):
    organization = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Organization.objects.all(),
    )

    class Meta:
        model = Control
        fields = (
            "uuid",
            "organization",
            "code",
            "title",
            "description",
            "domain",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("uuid", "created_at", "updated_at")


class RiskSerializer(OrganizationMembershipValidatorMixin, serializers.ModelSerializer):
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
        model = Risk
        fields = (
            "uuid",
            "organization",
            "ai_use_case",
            "title",
            "description",
            "likelihood",
            "impact",
            "severity",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("uuid", "created_at", "updated_at")

    def validate(self, attrs):
        organization = attrs.get("organization") or getattr(self.instance, "organization", None)
        ai_use_case = attrs.get("ai_use_case")
        if ai_use_case and organization and ai_use_case.organization_id != organization.id:
            raise serializers.ValidationError({"ai_use_case": "AI use case must belong to the same organization."})
        return attrs


class RiskControlSerializer(serializers.ModelSerializer):
    risk = serializers.SlugRelatedField(slug_field="uuid", queryset=Risk.objects.all())
    control = serializers.SlugRelatedField(slug_field="uuid", queryset=Control.objects.all())

    class Meta:
        model = RiskControl
        fields = ("id", "risk", "control", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_risk(self, risk):
        user = self.context["request"].user
        if user.is_superuser:
            return risk
        if risk.organization.memberships.filter(user=user, status=Membership.Status.ACTIVE).exists():
            return risk
        raise serializers.ValidationError("You are not a member of this risk organization.")

    def validate(self, attrs):
        risk = attrs.get("risk") or getattr(self.instance, "risk", None)
        control = attrs.get("control") or getattr(self.instance, "control", None)
        if risk and control and risk.organization_id != control.organization_id:
            raise serializers.ValidationError({"control": "Control must belong to the same organization as the risk."})
        return attrs

