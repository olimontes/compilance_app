from rest_framework import viewsets

from apps.audit.services import log_create_event
from apps.common.tenancy import OrganizationScopedQuerySetMixin

from .models import AiTool, AiUseCase, AiVendor
from .serializers import AiToolSerializer, AiUseCaseSerializer, AiVendorSerializer


class AiVendorViewSet(OrganizationScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = AiVendorSerializer
    lookup_field = "uuid"
    queryset = AiVendor.objects.none()

    def get_queryset(self):
        queryset = AiVendor.objects.filter(organization_id__in=self.user_organization_ids())
        risk_level = self.request.query_params.get("risk_level")
        if risk_level:
            queryset = queryset.filter(risk_level=risk_level)
        return queryset

    def perform_create(self, serializer):
        vendor = serializer.save()
        log_create_event(
            actor_user=self.request.user,
            organization=vendor.organization,
            instance=vendor,
            event_type="ai_vendor.created",
        )


class AiToolViewSet(OrganizationScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = AiToolSerializer
    lookup_field = "uuid"
    queryset = AiTool.objects.none()

    def get_queryset(self):
        queryset = AiTool.objects.filter(organization_id__in=self.user_organization_ids())
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def perform_create(self, serializer):
        tool = serializer.save()
        log_create_event(
            actor_user=self.request.user,
            organization=tool.organization,
            instance=tool,
            event_type="ai_tool.created",
        )


class AiUseCaseViewSet(OrganizationScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = AiUseCaseSerializer
    lookup_field = "uuid"
    queryset = AiUseCase.objects.none()

    def get_queryset(self):
        queryset = AiUseCase.objects.filter(organization_id__in=self.user_organization_ids())
        risk_level = self.request.query_params.get("risk_level")
        lifecycle_stage = self.request.query_params.get("lifecycle_stage")
        if risk_level:
            queryset = queryset.filter(risk_level=risk_level)
        if lifecycle_stage:
            queryset = queryset.filter(lifecycle_stage=lifecycle_stage)
        return queryset

    def perform_create(self, serializer):
        use_case = serializer.save()
        log_create_event(
            actor_user=self.request.user,
            organization=use_case.organization,
            instance=use_case,
            event_type="ai_use_case.created",
        )
