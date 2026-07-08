from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import Membership, Organization, OrganizationUnit


class OrganizationModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="alice",
            email="alice@example.com",
            password="password-123",
        )
        self.organization = Organization.objects.create(
            name="Acme Corp",
            slug="acme-corp",
        )

    def test_create_organization_membership(self):
        membership = Membership.objects.create(
            user=self.user,
            organization=self.organization,
            role=Membership.Role.OWNER,
        )

        self.assertEqual(membership.user, self.user)
        self.assertEqual(membership.organization, self.organization)
        self.assertTrue(membership.uuid)

    def test_membership_is_unique_per_user_and_organization(self):
        Membership.objects.create(user=self.user, organization=self.organization)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Membership.objects.create(user=self.user, organization=self.organization)

    def test_organization_unit_slug_is_unique_per_organization(self):
        OrganizationUnit.objects.create(
            organization=self.organization,
            name="Legal",
            slug="legal",
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            OrganizationUnit.objects.create(
                organization=self.organization,
                name="Legal Duplicate",
                slug="legal",
            )
