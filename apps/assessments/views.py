from rest_framework import viewsets

from apps.audit.services import log_create_event
from apps.organizations.models import Membership, Organization

from .models import (
    Assessment,
    AssessmentAnswer,
    AssessmentDimension,
    AssessmentFramework,
    AssessmentQuestion,
)
from .serializers import (
    AssessmentAnswerSerializer,
    AssessmentDimensionSerializer,
    AssessmentFrameworkSerializer,
    AssessmentQuestionSerializer,
    AssessmentSerializer,
)


class OrganizationScopedQuerySetMixin:
    def user_organization_ids(self):
        user = self.request.user
        if user.is_superuser:
            return Organization.objects.values_list("id", flat=True)
        return Membership.objects.filter(
            user=user,
            status=Membership.Status.ACTIVE,
        ).values_list("organization_id", flat=True)


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
