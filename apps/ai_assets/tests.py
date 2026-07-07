from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.organizations.models import Organization, OrganizationUnit

from .models import AiTool, AiUseCase, AiVendor, RiskLevel


class AiAssetModelTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Acme Corp",
            slug="acme-corp",
        )
        self.unit = OrganizationUnit.objects.create(
            organization=self.organization,
            name="Legal",
            slug="legal",
        )

    def test_create_ai_vendor_tool_and_use_case(self):
        vendor = AiVendor.objects.create(
            organization=self.organization,
            name="OpenAI",
            website="https://openai.com",
            risk_level=RiskLevel.HIGH,
        )
        tool = AiTool.objects.create(
            organization=self.organization,
            vendor=vendor,
            name="ChatGPT Enterprise",
            category="assistant",
            handles_personal_data=True,
        )
        use_case = AiUseCase.objects.create(
            organization=self.organization,
            ai_tool=tool,
            organization_unit=self.unit,
            name="Contract review",
            business_area="Legal",
            purpose="Support first-pass contract analysis.",
        )

        self.assertEqual(tool.vendor, vendor)
        self.assertEqual(use_case.ai_tool, tool)
        self.assertEqual(use_case.organization_unit, self.unit)
        self.assertTrue(use_case.uuid)

    def test_ai_tool_name_is_unique_per_organization(self):
        AiTool.objects.create(organization=self.organization, name="Copilot")

        with self.assertRaises(IntegrityError), transaction.atomic():
            AiTool.objects.create(organization=self.organization, name="Copilot")

