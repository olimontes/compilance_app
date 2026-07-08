from rest_framework import viewsets

from .models import Membership, Organization, OrganizationUnit
from .serializers import MembershipSerializer, OrganizationSerializer, OrganizationUnitSerializer


class OrganizationAccessMixin:
    def user_organization_ids(self):
        user = self.request.user
        if user.is_superuser:
            return Organization.objects.values_list("id", flat=True)
        return Membership.objects.filter(
            user=user,
            status=Membership.Status.ACTIVE,
        ).values_list("organization_id", flat=True)


class OrganizationViewSet(OrganizationAccessMixin, viewsets.ModelViewSet):
    serializer_class = OrganizationSerializer
    lookup_field = "uuid"
    queryset = Organization.objects.none()

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Organization.objects.all()
        return Organization.objects.filter(memberships__user=self.request.user).distinct()

    def perform_create(self, serializer):
        organization = serializer.save()
        Membership.objects.create(
            organization=organization,
            user=self.request.user,
            role=Membership.Role.OWNER,
            status=Membership.Status.ACTIVE,
        )


class OrganizationUnitViewSet(OrganizationAccessMixin, viewsets.ModelViewSet):
    serializer_class = OrganizationUnitSerializer
    lookup_field = "uuid"
    queryset = OrganizationUnit.objects.none()

    def get_queryset(self):
        return OrganizationUnit.objects.filter(organization_id__in=self.user_organization_ids())


class MembershipViewSet(OrganizationAccessMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = MembershipSerializer
    lookup_field = "uuid"
    queryset = Membership.objects.none()

    def get_queryset(self):
        return Membership.objects.filter(organization_id__in=self.user_organization_ids())
