from rest_framework import serializers

from apps.common.tenancy import user_has_active_membership

from .models import Membership, Organization, OrganizationUnit


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("uuid", "name", "slug", "tax_id", "status", "created_at", "updated_at")
        read_only_fields = ("uuid", "created_at", "updated_at")


class OrganizationUnitSerializer(serializers.ModelSerializer):
    organization = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=Organization.objects.all(),
    )
    parent = serializers.SlugRelatedField(
        slug_field="uuid",
        queryset=OrganizationUnit.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = OrganizationUnit
        fields = (
            "uuid",
            "organization",
            "parent",
            "name",
            "slug",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("uuid", "created_at", "updated_at")

    def validate_organization(self, organization):
        user = self.context["request"].user
        if user_has_active_membership(user, organization):
            return organization
        raise serializers.ValidationError("You are not a member of this organization.")

    def validate(self, attrs):
        organization = attrs.get("organization") or getattr(self.instance, "organization", None)
        parent = attrs.get("parent")
        if parent and organization and parent.organization_id != organization.id:
            raise serializers.ValidationError({"parent": "Parent unit must belong to the same organization."})
        return attrs


class MembershipSerializer(serializers.ModelSerializer):
    organization = serializers.SlugRelatedField(slug_field="uuid", read_only=True)
    user = serializers.SlugRelatedField(slug_field="uuid", read_only=True)

    class Meta:
        model = Membership
        fields = ("uuid", "organization", "user", "role", "status", "created_at", "updated_at")
        read_only_fields = fields
