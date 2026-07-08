from rest_framework import viewsets

from apps.audit.services import log_create_event
from apps.common.tenancy import OrganizationScopedQuerySetMixin

from .models import ActionItem, ActionPlan, Control, Policy, Risk, RiskAssessment, RiskControl
from .serializers import (
    ActionItemSerializer,
    ActionPlanSerializer,
    ControlSerializer,
    PolicySerializer,
    RiskAssessmentSerializer,
    RiskControlSerializer,
    RiskSerializer,
)


class ControlViewSet(OrganizationScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = ControlSerializer
    lookup_field = "uuid"
    queryset = Control.objects.none()

    def get_queryset(self):
        queryset = Control.objects.filter(organization_id__in=self.user_organization_ids())
        status = self.request.query_params.get("status")
        domain = self.request.query_params.get("domain")
        if status:
            queryset = queryset.filter(status=status)
        if domain:
            queryset = queryset.filter(domain=domain)
        return queryset

    def perform_create(self, serializer):
        control = serializer.save()
        log_create_event(
            actor_user=self.request.user,
            organization=control.organization,
            instance=control,
            event_type="control.created",
        )


class RiskViewSet(OrganizationScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = RiskSerializer
    lookup_field = "uuid"
    queryset = Risk.objects.none()

    def get_queryset(self):
        queryset = Risk.objects.filter(organization_id__in=self.user_organization_ids())
        status = self.request.query_params.get("status")
        severity = self.request.query_params.get("severity")
        if status:
            queryset = queryset.filter(status=status)
        if severity:
            queryset = queryset.filter(severity=severity)
        return queryset

    def perform_create(self, serializer):
        risk = serializer.save()
        log_create_event(
            actor_user=self.request.user,
            organization=risk.organization,
            instance=risk,
            event_type="risk.created",
        )


class RiskControlViewSet(OrganizationScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = RiskControlSerializer
    queryset = RiskControl.objects.none()

    def get_queryset(self):
        return RiskControl.objects.filter(risk__organization_id__in=self.user_organization_ids())


class RiskAssessmentViewSet(OrganizationScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = RiskAssessmentSerializer
    lookup_field = "uuid"
    queryset = RiskAssessment.objects.none()

    def get_queryset(self):
        queryset = RiskAssessment.objects.filter(
            risk__organization_id__in=self.user_organization_ids()
        ).select_related("risk", "assessed_by")
        risk = self.request.query_params.get("risk")
        severity = self.request.query_params.get("severity")
        if risk:
            queryset = queryset.filter(risk__uuid=risk)
        if severity:
            queryset = queryset.filter(severity=severity)
        return queryset

    def perform_create(self, serializer):
        risk_assessment = serializer.save()
        log_create_event(
            actor_user=self.request.user,
            organization=risk_assessment.risk.organization,
            instance=risk_assessment,
            event_type="risk_assessment.created",
        )


class PolicyViewSet(OrganizationScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = PolicySerializer
    lookup_field = "uuid"
    queryset = Policy.objects.none()

    def get_queryset(self):
        queryset = Policy.objects.filter(organization_id__in=self.user_organization_ids())
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def perform_create(self, serializer):
        policy = serializer.save()
        log_create_event(
            actor_user=self.request.user,
            organization=policy.organization,
            instance=policy,
            event_type="policy.created",
        )


class ActionPlanViewSet(OrganizationScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = ActionPlanSerializer
    lookup_field = "uuid"
    queryset = ActionPlan.objects.none()

    def get_queryset(self):
        queryset = ActionPlan.objects.filter(organization_id__in=self.user_organization_ids())
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def perform_create(self, serializer):
        action_plan = serializer.save()
        log_create_event(
            actor_user=self.request.user,
            organization=action_plan.organization,
            instance=action_plan,
            event_type="action_plan.created",
        )


class ActionItemViewSet(OrganizationScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = ActionItemSerializer
    lookup_field = "uuid"
    queryset = ActionItem.objects.none()

    def get_queryset(self):
        queryset = ActionItem.objects.filter(organization_id__in=self.user_organization_ids())
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def perform_create(self, serializer):
        action_item = serializer.save()
        log_create_event(
            actor_user=self.request.user,
            organization=action_item.organization,
            instance=action_item,
            event_type="action_item.created",
        )
