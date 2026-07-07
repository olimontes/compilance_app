from rest_framework import serializers

from apps.organizations.models import Membership, Organization

from .models import (
    Assessment,
    AssessmentAnswer,
    AssessmentDimension,
    AssessmentFramework,
    AssessmentQuestion,
)


class AssessmentFrameworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentFramework
        fields = ("uuid", "code", "name", "version", "status", "created_at", "updated_at")
        read_only_fields = ("uuid", "created_at", "updated_at")


class AssessmentDimensionSerializer(serializers.ModelSerializer):
    framework = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=AssessmentFramework.objects.all(),
    )

    class Meta:
        model = AssessmentDimension
        fields = (
            "uuid",
            "framework",
            "code",
            "name",
            "description",
            "display_order",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("uuid", "created_at", "updated_at")


class AssessmentQuestionSerializer(serializers.ModelSerializer):
    framework = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=AssessmentFramework.objects.all(),
    )
    dimension = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=AssessmentDimension.objects.all(),
    )

    class Meta:
        model = AssessmentQuestion
        fields = (
            "uuid",
            "framework",
            "dimension",
            "code",
            "text",
            "answer_type",
            "weight",
            "is_required",
            "display_order",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("uuid", "created_at", "updated_at")

    def validate(self, attrs):
        framework = attrs.get("framework") or getattr(self.instance, "framework", None)
        dimension = attrs.get("dimension")
        if dimension and framework and dimension.framework_id != framework.id:
            raise serializers.ValidationError({"dimension": "Dimension must belong to the same framework."})
        return attrs


class OrganizationMembershipValidatorMixin:
    def validate_organization(self, organization):
        user = self.context["request"].user
        if user.is_superuser:
            return organization
        if organization.memberships.filter(user=user, status=Membership.Status.ACTIVE).exists():
            return organization
        raise serializers.ValidationError("You are not a member of this organization.")


class AssessmentSerializer(OrganizationMembershipValidatorMixin, serializers.ModelSerializer):
    organization = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Organization.objects.all(),
    )
    framework = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=AssessmentFramework.objects.all(),
    )
    created_by = serializers.SlugRelatedField(slug_field="uuid", read_only=True)

    class Meta:
        model = Assessment
        fields = (
            "uuid",
            "organization",
            "framework",
            "created_by",
            "title",
            "status",
            "started_at",
            "submitted_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("uuid", "created_by", "created_at", "updated_at")


class AssessmentAnswerSerializer(serializers.ModelSerializer):
    assessment = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Assessment.objects.all(),
    )
    question = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=AssessmentQuestion.objects.all(),
    )
    answered_by = serializers.SlugRelatedField(slug_field="uuid", read_only=True)

    class Meta:
        model = AssessmentAnswer
        fields = (
            "uuid",
            "assessment",
            "question",
            "answered_by",
            "value",
            "score",
            "notes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("uuid", "answered_by", "created_at", "updated_at")

    def validate_assessment(self, assessment):
        user = self.context["request"].user
        if user.is_superuser:
            return assessment
        if assessment.organization.memberships.filter(user=user, status=Membership.Status.ACTIVE).exists():
            return assessment
        raise serializers.ValidationError("You are not a member of this assessment organization.")

    def validate(self, attrs):
        assessment = attrs.get("assessment") or getattr(self.instance, "assessment", None)
        question = attrs.get("question")
        if assessment and question and question.framework_id != assessment.framework_id:
            raise serializers.ValidationError({"question": "Question must belong to the assessment framework."})
        return attrs

