from rest_framework import viewsets

from apps.audit.services import log_create_event
from apps.common.tenancy import OrganizationScopedQuerySetMixin

from .models import AiAssetOwner, AiModel, AiTool, AiUseCase, AiVendor, DataSource
from .serializers import (
    AiAssetOwnerSerializer,
    AiModelSerializer,
    AiToolSerializer,
    AiUseCaseSerializer,
    AiVendorSerializer,
    DataSourceSerializer,
)


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


class AiModelViewSet(OrganizationScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = AiModelSerializer
    lookup_field = "uuid"
    queryset = AiModel.objects.none()

    def get_queryset(self):
        queryset = AiModel.objects.filter(organization_id__in=self.user_organization_ids())
        status = self.request.query_params.get("status")
        risk_level = self.request.query_params.get("risk_level")
        model_type = self.request.query_params.get("model_type")
        if status:
            queryset = queryset.filter(status=status)
        if risk_level:
            queryset = queryset.filter(risk_level=risk_level)
        if model_type:
            queryset = queryset.filter(model_type=model_type)
        return queryset

    def perform_create(self, serializer):
        ai_model = serializer.save()
        log_create_event(
            actor_user=self.request.user,
            organization=ai_model.organization,
            instance=ai_model,
            event_type="ai_model.created",
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


class DataSourceViewSet(OrganizationScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = DataSourceSerializer
    lookup_field = "uuid"
    queryset = DataSource.objects.none()

    def get_queryset(self):
        queryset = DataSource.objects.filter(organization_id__in=self.user_organization_ids())
        source_type = self.request.query_params.get("source_type")
        data_classification = self.request.query_params.get("data_classification")
        if source_type:
            queryset = queryset.filter(source_type=source_type)
        if data_classification:
            queryset = queryset.filter(data_classification=data_classification)
        return queryset

    def perform_create(self, serializer):
        data_source = serializer.save()
        log_create_event(
            actor_user=self.request.user,
            organization=data_source.organization,
            instance=data_source,
            event_type="data_source.created",
        )


class AiAssetOwnerViewSet(OrganizationScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = AiAssetOwnerSerializer
    lookup_field = "uuid"
    queryset = AiAssetOwner.objects.none()

    def get_queryset(self):
        queryset = AiAssetOwner.objects.filter(organization_id__in=self.user_organization_ids())
        responsibility = self.request.query_params.get("responsibility")
        if responsibility:
            queryset = queryset.filter(responsibility=responsibility)
        return queryset

    def perform_create(self, serializer):
        owner = serializer.save()
        log_create_event(
            actor_user=self.request.user,
            organization=owner.organization,
            instance=owner,
            event_type="ai_asset_owner.created",
        )
