from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.audit.models import AuditEvent
from apps.organizations.models import Membership, Organization, OrganizationUnit

from .models import AiAssetOwner, AiModel, AiTool, AiUseCase, AiVendor, DataSource, RiskLevel


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
        self.assertTrue(AuditEvent.objects.filter(event_type="ai_vendor.created").exists())

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
        self.assertTrue(AuditEvent.objects.filter(event_type="ai_tool.created").exists())
        self.assertTrue(AuditEvent.objects.filter(event_type="ai_use_case.created").exists())

    def test_create_ai_model(self):
        tool = AiTool.objects.create(organization=self.organization, name="ChatGPT Enterprise")

        response = self.client.post(
            "/api/ai-models/",
            {
                "organization": str(self.organization.uuid),
                "ai_tool": str(tool.uuid),
                "name": "GPT-4.1",
                "provider_model_id": "gpt-4.1",
                "model_type": AiModel.ModelType.TEXT,
                "status": AiModel.Status.ACTIVE,
                "risk_level": RiskLevel.HIGH,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(AiModel.objects.filter(name="GPT-4.1").exists())
        self.assertTrue(AuditEvent.objects.filter(event_type="ai_model.created").exists())

    def test_create_data_source_and_asset_owner(self):
        use_case = AiUseCase.objects.create(
            organization=self.organization,
            name="Contract review",
            purpose="Support first-pass contract analysis.",
        )
        membership = Membership.objects.get(user=self.user, organization=self.organization)

        data_source_response = self.client.post(
            "/api/data-sources/",
            {
                "organization": str(self.organization.uuid),
                "ai_use_case": str(use_case.uuid),
                "name": "Contract repository",
                "source_type": DataSource.SourceType.DOCUMENT,
                "data_classification": AiUseCase.DataClassification.CONFIDENTIAL,
                "contains_personal_data": True,
                "contains_sensitive_data": False,
            },
            format="json",
        )

        self.assertEqual(data_source_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(DataSource.objects.filter(name="Contract repository").exists())

        owner_response = self.client.post(
            "/api/ai-asset-owners/",
            {
                "organization": str(self.organization.uuid),
                "ai_use_case": str(use_case.uuid),
                "membership": str(membership.uuid),
                "responsibility": AiAssetOwner.Responsibility.BUSINESS_OWNER,
            },
            format="json",
        )

        self.assertEqual(owner_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(AiAssetOwner.objects.filter(ai_use_case=use_case, membership=membership).exists())
        self.assertTrue(AuditEvent.objects.filter(event_type="data_source.created").exists())
        self.assertTrue(AuditEvent.objects.filter(event_type="ai_asset_owner.created").exists())

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

    def test_create_ai_model_rejects_tool_from_another_organization(self):
        hidden_org = Organization.objects.create(name="Hidden Corp", slug="hidden-corp")
        hidden_tool = AiTool.objects.create(organization=hidden_org, name="Hidden Tool")

        response = self.client.post(
            "/api/ai-models/",
            {
                "organization": str(self.organization.uuid),
                "ai_tool": str(hidden_tool.uuid),
                "name": "Cross tenant model",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_asset_owner_rejects_membership_from_another_organization(self):
        hidden_org = Organization.objects.create(name="Hidden Corp", slug="hidden-corp")
        hidden_user = get_user_model().objects.create_user(username="hidden", email="hidden@example.com")
        hidden_membership = Membership.objects.create(user=hidden_user, organization=hidden_org)
        use_case = AiUseCase.objects.create(
            organization=self.organization,
            name="Contract review",
            purpose="Support first-pass contract analysis.",
        )

        response = self.client.post(
            "/api/ai-asset-owners/",
            {
                "organization": str(self.organization.uuid),
                "ai_use_case": str(use_case.uuid),
                "membership": str(hidden_membership.uuid),
                "responsibility": AiAssetOwner.Responsibility.BUSINESS_OWNER,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
