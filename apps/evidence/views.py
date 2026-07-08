from rest_framework import viewsets

from apps.audit.services import log_create_event
from apps.organizations.models import Membership, Organization

from .models import Evidence, EvidenceLink
from .serializers import EvidenceLinkSerializer, EvidenceSerializer


class OrganizationScopedQuerySetMixin:
    def user_organization_ids(self):
        user = self.request.user
        if user.is_superuser:
            return Organization.objects.values_list("id", flat=True)
        return Membership.objects.filter(
            user=user,
            status=Membership.Status.ACTIVE,
        ).values_list("organization_id", flat=True)


class EvidenceViewSet(OrganizationScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = EvidenceSerializer
    lookup_field = "uuid"
    queryset = Evidence.objects.none()

    def get_queryset(self):
        queryset = Evidence.objects.filter(organization_id__in=self.user_organization_ids())
        status = self.request.query_params.get("status")
        evidence_type = self.request.query_params.get("evidence_type")
        if status:
            queryset = queryset.filter(status=status)
        if evidence_type:
            queryset = queryset.filter(evidence_type=evidence_type)
        return queryset

    def perform_create(self, serializer):
        evidence = serializer.save(uploaded_by=self.request.user)
        log_create_event(
            actor_user=self.request.user,
            organization=evidence.organization,
            instance=evidence,
            event_type="evidence.uploaded",
        )


class EvidenceLinkViewSet(OrganizationScopedQuerySetMixin, viewsets.ModelViewSet):
    serializer_class = EvidenceLinkSerializer
    queryset = EvidenceLink.objects.none()

    def get_queryset(self):
        return EvidenceLink.objects.filter(evidence__organization_id__in=self.user_organization_ids())
