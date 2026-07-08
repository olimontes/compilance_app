from rest_framework import serializers

from apps.organizations.models import Membership, Organization


def active_organization_ids_for_user(user):
    if user.is_superuser:
        return Organization.objects.values_list("id", flat=True)
    return Membership.objects.filter(
        user=user,
        status=Membership.Status.ACTIVE,
    ).values_list("organization_id", flat=True)


def user_has_active_membership(user, organization):
    if user.is_superuser:
        return True
    return organization.memberships.filter(
        user=user,
        status=Membership.Status.ACTIVE,
    ).exists()


class OrganizationScopedQuerySetMixin:
    def user_organization_ids(self):
        return active_organization_ids_for_user(self.request.user)


class OrganizationMembershipValidatorMixin:
    def validate_organization(self, organization):
        user = self.context["request"].user
        if user_has_active_membership(user, organization):
            return organization
        raise serializers.ValidationError("You are not a member of this organization.")
