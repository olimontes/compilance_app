from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Membership, Organization, OrganizationUnit


class OrganizationApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="alice",
            email="alice@example.com",
            password="password-123",
        )
        self.client.force_authenticate(self.user)

    def test_create_organization_adds_owner_membership(self):
        response = self.client.post(
            "/api/organizations/",
            {
                "name": "Acme Corp",
                "slug": "acme-corp",
                "tax_id": "",
                "status": Organization.Status.ACTIVE,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Membership.objects.filter(
                user=self.user,
                organization__slug="acme-corp",
                role=Membership.Role.OWNER,
            ).exists()
        )

    def test_list_organizations_only_returns_user_memberships(self):
        visible = Organization.objects.create(name="Visible", slug="visible")
        hidden = Organization.objects.create(name="Hidden", slug="hidden")
        inactive = Organization.objects.create(name="Inactive", slug="inactive")
        Membership.objects.create(user=self.user, organization=visible)
        Membership.objects.create(
            user=self.user,
            organization=inactive,
            status=Membership.Status.INACTIVE,
        )

        response = self.client.get("/api/organizations/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = {item["name"] for item in response.json()["results"]}
        self.assertIn(visible.name, names)
        self.assertNotIn(hidden.name, names)
        self.assertNotIn(inactive.name, names)

    def test_create_organization_unit_for_member_organization(self):
        organization = Organization.objects.create(name="Acme Corp", slug="acme-corp")
        Membership.objects.create(user=self.user, organization=organization)

        response = self.client.post(
            "/api/organization-units/",
            {
                "organization": str(organization.uuid),
                "name": "Legal",
                "slug": "legal",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(OrganizationUnit.objects.filter(slug="legal").exists())
