from rest_framework import serializers

from apps.ai_assets.models import AiUseCase
from apps.common.tenancy import OrganizationMembershipValidatorMixin, user_has_active_membership
from apps.organizations.models import Membership, Organization

from .models import ActionItem, ActionPlan, Control, Policy, Risk, RiskAssessment, RiskControl


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
        if user_has_active_membership(user, risk.organization):
            return risk
        raise serializers.ValidationError("You are not a member of this risk organization.")

    def validate(self, attrs):
        risk = attrs.get("risk") or getattr(self.instance, "risk", None)
        control = attrs.get("control") or getattr(self.instance, "control", None)
        if risk and control and risk.organization_id != control.organization_id:
            raise serializers.ValidationError({"control": "Control must belong to the same organization as the risk."})
        return attrs


class RiskAssessmentSerializer(serializers.ModelSerializer):
    risk = serializers.SlugRelatedField(slug_field="uuid", queryset=Risk.objects.all())
    assessed_by = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Membership.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = RiskAssessment
        fields = (
            "uuid",
            "risk",
            "assessed_by",
            "likelihood",
            "impact",
            "severity",
            "rationale",
            "assessed_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("uuid", "created_at", "updated_at")

    def validate_risk(self, risk):
        user = self.context["request"].user
        if user_has_active_membership(user, risk.organization):
            return risk
        raise serializers.ValidationError("You are not a member of this risk organization.")

    def validate(self, attrs):
        risk = attrs.get("risk") or getattr(self.instance, "risk", None)
        assessed_by = attrs.get("assessed_by")
        if risk and assessed_by and risk.organization_id != assessed_by.organization_id:
            raise serializers.ValidationError({"assessed_by": "Membership must belong to the risk organization."})
        return attrs


class PolicySerializer(OrganizationMembershipValidatorMixin, serializers.ModelSerializer):
    organization = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Organization.objects.all(),
    )
    owner_membership = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Membership.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Policy
        fields = (
            "uuid",
            "organization",
            "code",
            "title",
            "description",
            "owner_membership",
            "status",
            "effective_date",
            "review_date",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("uuid", "created_at", "updated_at")

    def validate(self, attrs):
        organization = attrs.get("organization") or getattr(self.instance, "organization", None)
        owner_membership = attrs.get("owner_membership")
        if owner_membership and organization and owner_membership.organization_id != organization.id:
            raise serializers.ValidationError({"owner_membership": "Membership must belong to the same organization."})
        return attrs


class ActionPlanSerializer(OrganizationMembershipValidatorMixin, serializers.ModelSerializer):
    organization = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Organization.objects.all(),
    )
    risk = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Risk.objects.all(),
        required=False,
        allow_null=True,
    )
    control = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Control.objects.all(),
        required=False,
        allow_null=True,
    )
    policy = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Policy.objects.all(),
        required=False,
        allow_null=True,
    )
    owner_membership = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Membership.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = ActionPlan
        fields = (
            "uuid",
            "organization",
            "risk",
            "control",
            "policy",
            "title",
            "description",
            "status",
            "due_date",
            "owner_membership",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("uuid", "created_at", "updated_at")

    def validate(self, attrs):
        organization = attrs.get("organization") or getattr(self.instance, "organization", None)
        related_fields = {
            "risk": attrs.get("risk"),
            "control": attrs.get("control"),
            "policy": attrs.get("policy"),
            "owner_membership": attrs.get("owner_membership"),
        }
        errors = {}
        for field_name, value in related_fields.items():
            if value and organization and value.organization_id != organization.id:
                errors[field_name] = "Related object must belong to the same organization."
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class ActionItemSerializer(OrganizationMembershipValidatorMixin, serializers.ModelSerializer):
    organization = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Organization.objects.all(),
    )
    action_plan = serializers.SlugRelatedField(slug_field="uuid", queryset=ActionPlan.objects.all())
    risk = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Risk.objects.all(),
        required=False,
        allow_null=True,
    )
    control = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Control.objects.all(),
        required=False,
        allow_null=True,
    )
    owner_membership = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Membership.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = ActionItem
        fields = (
            "uuid",
            "organization",
            "action_plan",
            "risk",
            "control",
            "title",
            "description",
            "status",
            "due_date",
            "owner_membership",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("uuid", "created_at", "updated_at")

    def validate(self, attrs):
        organization = attrs.get("organization") or getattr(self.instance, "organization", None)
        related_fields = {
            "action_plan": attrs.get("action_plan"),
            "risk": attrs.get("risk"),
            "control": attrs.get("control"),
            "owner_membership": attrs.get("owner_membership"),
        }
        errors = {}
        for field_name, value in related_fields.items():
            if value and organization and value.organization_id != organization.id:
                errors[field_name] = "Related object must belong to the same organization."
        if errors:
            raise serializers.ValidationError(errors)
        return attrs
