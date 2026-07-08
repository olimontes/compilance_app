from rest_framework import viewsets

from apps.audit.services import log_create_event
from apps.common.tenancy import OrganizationScopedQuerySetMixin

from .models import (
    Assessment,
    AssessmentAnswer,
    AssessmentDimension,
    AssessmentFramework,
    AssessmentQuestion,
    MaturityScore,
    Recommendation,
)
from .serializers import (
    AssessmentAnswerSerializer,
    AssessmentDimensionSerializer,
    AssessmentFrameworkSerializer,
    AssessmentQuestionSerializer,
    AssessmentSerializer,
    MaturityScoreSerializer,
    RecommendationSerializer,
)


class AssessmentFrameworkViewSet(viewsets.ModelViewSet):
    serializer_class = AssessmentFrameworkSerializer
    lookup_field = "uuid"
    queryset = AssessmentFramework.objects.all()


class AssessmentDimensionViewSet(viewsets.ModelViewSet):
    serializer_class = AssessmentDimensionSerializer
    lookup_field = "uuid"
    queryset = AssessmentDimension.objects.select_related("framework")


class AssessmentQuestionViewSet(viewsets.ModelViewSet):
    serializer_class = AssessmentQuestionSerializer
    lookup_field = "uuid"

    def get_queryset(self):
        queryset = AssessmentQuestion.objects.select_related("framework", "dimension")
        framework = self.request.query_params.get("framework")
        if framework:
            queryset = queryset.filter(framework__uuid=framework)
        return queryset


class AssessmentViewSet(OrganizationScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = AssessmentSerializer
    lookup_field = "uuid"
    queryset = Assessment.objects.none()

    def get_queryset(self):
        queryset = Assessment.objects.filter(organization_id__in=self.user_organization_ids())
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def perform_create(self, serializer):
        assessment = serializer.save(created_by=self.request.user)
        log_create_event(
            actor_user=self.request.user,
            organization=assessment.organization,
            instance=assessment,
            event_type="assessment.started",
        )


class AssessmentAnswerViewSet(OrganizationScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = AssessmentAnswerSerializer
    lookup_field = "uuid"
    queryset = AssessmentAnswer.objects.none()

    def get_queryset(self):
        return AssessmentAnswer.objects.filter(
            assessment__organization_id__in=self.user_organization_ids()
        ).select_related("assessment", "question", "answered_by")

    def perform_create(self, serializer):
        answer = serializer.save(answered_by=self.request.user)
        log_create_event(
            actor_user=self.request.user,
            organization=answer.assessment.organization,
            instance=answer,
            event_type="assessment_answer.created",
        )


class MaturityScoreViewSet(OrganizationScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = MaturityScoreSerializer
    lookup_field = "uuid"
    queryset = MaturityScore.objects.none()

    def get_queryset(self):
        queryset = MaturityScore.objects.filter(
            assessment__organization_id__in=self.user_organization_ids()
        ).select_related("assessment", "dimension")
        assessment = self.request.query_params.get("assessment")
        if assessment:
            queryset = queryset.filter(assessment__uuid=assessment)
        return queryset

    def perform_create(self, serializer):
        maturity_score = serializer.save()
        log_create_event(
            actor_user=self.request.user,
            organization=maturity_score.assessment.organization,
            instance=maturity_score,
            event_type="maturity_score.created",
        )


class RecommendationViewSet(OrganizationScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = RecommendationSerializer
    lookup_field = "uuid"
    queryset = Recommendation.objects.none()

    def get_queryset(self):
        queryset = Recommendation.objects.filter(
            assessment__organization_id__in=self.user_organization_ids()
        ).select_related("assessment", "dimension")
        status = self.request.query_params.get("status")
        priority = self.request.query_params.get("priority")
        if status:
            queryset = queryset.filter(status=status)
        if priority:
            queryset = queryset.filter(priority=priority)
        return queryset

    def perform_create(self, serializer):
        recommendation = serializer.save()
        log_create_event(
            actor_user=self.request.user,
            organization=recommendation.assessment.organization,
            instance=recommendation,
            event_type="recommendation.created",
        )
