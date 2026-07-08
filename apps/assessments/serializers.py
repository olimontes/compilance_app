from rest_framework import serializers

from apps.common.tenancy import (
    OrganizationMembershipValidatorMixin,
    serializer_field_value,
    user_has_active_membership,
)
from apps.organizations.models import Organization

from .models import (
    Assessment,
    AssessmentAnswer,
    AssessmentDimension,
    AssessmentFramework,
    AssessmentQuestion,
    MaturityScore,
    Recommendation,
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
        framework = serializer_field_value(self, attrs, "framework")
        dimension = serializer_field_value(self, attrs, "dimension")
        if dimension and framework and dimension.framework_id != framework.id:
            raise serializers.ValidationError({"dimension": "Dimension must belong to the same framework."})
        return attrs


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
        if user_has_active_membership(user, assessment.organization):
            return assessment
        raise serializers.ValidationError("You are not a member of this assessment organization.")

    def validate(self, attrs):
        assessment = serializer_field_value(self, attrs, "assessment")
        question = serializer_field_value(self, attrs, "question")
        if assessment and question and question.framework_id != assessment.framework_id:
            raise serializers.ValidationError({"question": "Question must belong to the assessment framework."})
        return attrs


class MaturityScoreSerializer(serializers.ModelSerializer):
    assessment = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Assessment.objects.all(),
    )
    dimension = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=AssessmentDimension.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = MaturityScore
        fields = (
            "uuid",
            "assessment",
            "dimension",
            "score",
            "max_score",
            "percentage",
            "computed_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("uuid", "created_at", "updated_at")

    def validate_assessment(self, assessment):
        user = self.context["request"].user
        if user_has_active_membership(user, assessment.organization):
            return assessment
        raise serializers.ValidationError("You are not a member of this assessment organization.")

    def validate(self, attrs):
        assessment = serializer_field_value(self, attrs, "assessment")
        dimension = serializer_field_value(self, attrs, "dimension")
        if assessment and dimension and dimension.framework_id != assessment.framework_id:
            raise serializers.ValidationError({"dimension": "Dimension must belong to the assessment framework."})
        return attrs


class RecommendationSerializer(serializers.ModelSerializer):
    assessment = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Assessment.objects.all(),
    )
    dimension = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=AssessmentDimension.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Recommendation
        fields = (
            "uuid",
            "assessment",
            "dimension",
            "title",
            "description",
            "priority",
            "status",
            "due_date",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("uuid", "created_at", "updated_at")

    def validate_assessment(self, assessment):
        user = self.context["request"].user
        if user_has_active_membership(user, assessment.organization):
            return assessment
        raise serializers.ValidationError("You are not a member of this assessment organization.")

    def validate(self, attrs):
        assessment = serializer_field_value(self, attrs, "assessment")
        dimension = serializer_field_value(self, attrs, "dimension")
        if assessment and dimension and dimension.framework_id != assessment.framework_id:
            raise serializers.ValidationError({"dimension": "Dimension must belong to the assessment framework."})
        return attrs
