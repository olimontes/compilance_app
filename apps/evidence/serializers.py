from rest_framework import serializers

from apps.assessments.models import AssessmentAnswer
from apps.common.tenancy import OrganizationMembershipValidatorMixin, user_has_active_membership
from apps.compliance.models import Control, Risk
from apps.organizations.models import Organization

from .models import Evidence, EvidenceLink


class EvidenceSerializer(OrganizationMembershipValidatorMixin, serializers.ModelSerializer):
    organization = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Organization.objects.all(),
    )
    uploaded_by = serializers.SlugRelatedField(slug_field="uuid", read_only=True)

    class Meta:
        model = Evidence
        fields = (
            "uuid",
            "organization",
            "uploaded_by",
            "title",
            "description",
            "evidence_type",
            "storage_backend",
            "file_path",
            "external_url",
            "checksum",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("uuid", "uploaded_by", "created_at", "updated_at")


class EvidenceLinkSerializer(serializers.ModelSerializer):
    evidence = serializers.SlugRelatedField(slug_field="uuid", queryset=Evidence.objects.all())
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
    assessment_answer = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=AssessmentAnswer.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = EvidenceLink
        fields = ("id", "evidence", "risk", "control", "assessment_answer", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_evidence(self, evidence):
        user = self.context["request"].user
        if user_has_active_membership(user, evidence.organization):
            return evidence
        raise serializers.ValidationError("You are not a member of this evidence organization.")

    def validate(self, attrs):
        evidence = attrs.get("evidence") or getattr(self.instance, "evidence", None)
        targets = [
            attrs.get("risk") or getattr(self.instance, "risk", None),
            attrs.get("control") or getattr(self.instance, "control", None),
            attrs.get("assessment_answer") or getattr(self.instance, "assessment_answer", None),
        ]
        selected_targets = [target for target in targets if target is not None]
        if len(selected_targets) != 1:
            raise serializers.ValidationError("Evidence link must have exactly one target.")

        target = selected_targets[0]
        if evidence and not self._target_belongs_to_evidence_organization(target, evidence):
            raise serializers.ValidationError("Evidence link target must belong to the same organization.")
        return attrs

    def _target_belongs_to_evidence_organization(self, target, evidence):
        if isinstance(target, AssessmentAnswer):
            return target.assessment.organization_id == evidence.organization_id
        return target.organization_id == evidence.organization_id
