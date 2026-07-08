from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.organizations.models import Membership, Organization, OrganizationUnit

from .models import AiTool, AiUseCase, AiVendor, RiskLevel


class AiAssetApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="alice",
            email="alice@example.com",
            password="password-123",
        )
        self.organization = Organization.objects.create(name="Acme Corp", slug="acme-corp")
        Membership.objects.create(user=self.user, organization=self.organization)
        self.client.force_authenticate(self.user)

    def test_create_ai_vendor(self):
        response = self.client.post(
            "/api/ai-vendors/",
            {
                "organization": str(self.organization.uuid),
                "name": "OpenAI",
                "website": "https://openai.com",
                "risk_level": RiskLevel.HIGH,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(AiVendor.objects.filter(name="OpenAI").exists())

    def test_create_ai_tool_and_use_case(self):
        vendor = AiVendor.objects.create(organization=self.organization, name="OpenAI")
        unit = OrganizationUnit.objects.create(
            organization=self.organization,
            name="Legal",
            slug="legal",
        )

        tool_response = self.client.post(
            "/api/ai-tools/",
            {
                "organization": str(self.organization.uuid),
                "vendor": str(vendor.uuid),
                "name": "ChatGPT Enterprise",
                "category": "assistant",
                "status": AiTool.Status.ACTIVE,
                "handles_personal_data": True,
                "handles_sensitive_data": False,
            },
            format="json",
        )

        self.assertEqual(tool_response.status_code, status.HTTP_201_CREATED)
        tool = AiTool.objects.get(name="ChatGPT Enterprise")

        use_case_response = self.client.post(
            "/api/ai-use-cases/",
            {
                "organization": str(self.organization.uuid),
                "ai_tool": str(tool.uuid),
                "organization_unit": str(unit.uuid),
                "name": "Contract review",
                "business_area": "Legal",
                "purpose": "Support first-pass contract analysis.",
                "data_classification": AiUseCase.DataClassification.CONFIDENTIAL,
                "risk_level": RiskLevel.HIGH,
                "lifecycle_stage": AiUseCase.LifecycleStage.PILOT,
            },
            format="json",
        )

        self.assertEqual(use_case_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(AiUseCase.objects.filter(name="Contract review").exists())

    def test_list_ai_tools_only_returns_user_organizations(self):
        hidden_org = Organization.objects.create(name="Hidden Corp", slug="hidden-corp")
        visible_tool = AiTool.objects.create(organization=self.organization, name="Visible Tool")
        AiTool.objects.create(organization=hidden_org, name="Hidden Tool")

        response = self.client.get("/api/ai-tools/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = {item["name"] for item in response.json()["results"]}
        self.assertIn(visible_tool.name, names)
        self.assertNotIn("Hidden Tool", names)

    def test_create_ai_tool_rejects_vendor_from_another_organization(self):
        hidden_org = Organization.objects.create(name="Hidden Corp", slug="hidden-corp")
        hidden_vendor = AiVendor.objects.create(organization=hidden_org, name="Hidden Vendor")

        response = self.client.post(
            "/api/ai-tools/",
            {
                "organization": str(self.organization.uuid),
                "vendor": str(hidden_vendor.uuid),
                "name": "Cross tenant tool",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
