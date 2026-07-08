from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.organizations.models import Organization

from .models import Control


class SeedControlsCommandTests(TestCase):
    def test_seed_controls_is_idempotent_for_organization(self):
        organization = Organization.objects.create(name="Acme Corp", slug="acme-corp")
        output = StringIO()

        call_command("seed_controls", organization_slug=organization.slug, stdout=output)
        call_command("seed_controls", organization_slug=organization.slug, stdout=output)

        self.assertEqual(Control.objects.filter(organization=organization).count(), 5)
        self.assertTrue(Control.objects.filter(organization=organization, code="GOV-001").exists())
        self.assertIn("Seeded 5 controls", output.getvalue())

    def test_seed_controls_requires_existing_organization(self):
        with self.assertRaises(CommandError):
            call_command("seed_controls", organization_slug="missing")
