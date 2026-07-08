from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.ai_assets.models import AiTool, AiUseCase, RiskLevel
from apps.audit.models import AuditEvent
from apps.organizations.models import Membership, Organization

from .models import Control, Risk, RiskControl


class ComplianceApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="alice",
            email="alice@example.com",
            password="password-123",
        )
        self.organization = Organization.objects.create(name="Acme Corp", slug="acme-corp")
        Membership.objects.create(user=self.user, organization=self.organization)
        self.tool = AiTool.objects.create(organization=self.organization, name="Contract Assistant")
        self.use_case = AiUseCase.objects.create(
            organization=self.organization,
            ai_tool=self.tool,
            name="Contract review",
            purpose="Support first-pass contract analysis.",
        )
        self.client.force_authenticate(self.user)

    def test_create_control_and_risk(self):
        control_response = self.client.post(
            "/api/controls/",
            {
                "organization": str(self.organization.uuid),
                "code": "CTRL-001",
                "title": "Access review",
                "description": "Review access quarterly.",
                "domain": "security",
                "status": Control.Status.ACTIVE,
            },
            format="json",
        )
        risk_response = self.client.post(
            "/api/risks/",
            {
                "organization": str(self.organization.uuid),
                "ai_use_case": str(self.use_case.uuid),
                "title": "Confidential information exposure",
                "description": "Contracts may include confidential clauses.",
                "likelihood": 3,
                "impact": 4,
                "severity": RiskLevel.HIGH,
                "status": Risk.Status.OPEN,
            },
            format="json",
        )

        self.assertEqual(control_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(risk_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Control.objects.filter(code="CTRL-001").exists())
        self.assertTrue(Risk.objects.filter(title="Confidential information exposure").exists())
        self.assertTrue(AuditEvent.objects.filter(event_type="control.created").exists())
        self.assertTrue(AuditEvent.objects.filter(event_type="risk.created").exists())

    def test_create_risk_control_link(self):
        control = Control.objects.create(
            organization=self.organization,
            code="CTRL-001",
            title="Access review",
        )
        risk = Risk.objects.create(
            organization=self.organization,
            ai_use_case=self.use_case,
            title="Confidential information exposure",
            likelihood=3,
            impact=4,
            severity=RiskLevel.HIGH,
        )

        response = self.client.post(
            "/api/risk-controls/",
            {
                "risk": str(risk.uuid),
                "control": str(control.uuid),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(RiskControl.objects.filter(risk=risk, control=control).exists())

    def test_list_risks_only_returns_user_organizations(self):
        hidden_org = Organization.objects.create(name="Hidden Corp", slug="hidden-corp")
        visible_risk = Risk.objects.create(
            organization=self.organization,
            title="Visible risk",
            likelihood=2,
            impact=3,
            severity=RiskLevel.MEDIUM,
        )
        Risk.objects.create(
            organization=hidden_org,
            title="Hidden risk",
            likelihood=2,
            impact=3,
            severity=RiskLevel.MEDIUM,
        )

        response = self.client.get("/api/risks/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = {item["title"] for item in response.json()["results"]}
        self.assertIn(visible_risk.title, titles)
        self.assertNotIn("Hidden risk", titles)

    def test_create_risk_rejects_use_case_from_another_organization(self):
        hidden_org = Organization.objects.create(name="Hidden Corp", slug="hidden-corp")
        hidden_tool = AiTool.objects.create(organization=hidden_org, name="Hidden Tool")
        hidden_use_case = AiUseCase.objects.create(
            organization=hidden_org,
            ai_tool=hidden_tool,
            name="Hidden use case",
            purpose="Hidden purpose.",
        )

        response = self.client.post(
            "/api/risks/",
            {
                "organization": str(self.organization.uuid),
                "ai_use_case": str(hidden_use_case.uuid),
                "title": "Cross tenant risk",
                "likelihood": 3,
                "impact": 4,
                "severity": RiskLevel.HIGH,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
