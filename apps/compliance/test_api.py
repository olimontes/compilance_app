from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.ai_assets.models import AiTool, AiUseCase, RiskLevel
from apps.audit.models import AuditEvent
from apps.organizations.models import Membership, Organization

from .models import ActionItem, ActionPlan, Control, Policy, Risk, RiskAssessment, RiskControl


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

    def test_create_risk_assessment_policy_action_plan_and_item(self):
        membership = Membership.objects.get(user=self.user, organization=self.organization)
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

        risk_assessment_response = self.client.post(
            "/api/risk-assessments/",
            {
                "risk": str(risk.uuid),
                "assessed_by": str(membership.uuid),
                "likelihood": 4,
                "impact": 4,
                "severity": RiskLevel.HIGH,
                "rationale": "Sensitive contracts are processed.",
                "assessed_at": timezone.now().isoformat(),
            },
            format="json",
        )

        policy_response = self.client.post(
            "/api/policies/",
            {
                "organization": str(self.organization.uuid),
                "code": "POL-001",
                "title": "AI acceptable use",
                "description": "Rules for approved AI usage.",
                "owner_membership": str(membership.uuid),
                "status": Policy.Status.ACTIVE,
            },
            format="json",
        )

        self.assertEqual(risk_assessment_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(policy_response.status_code, status.HTTP_201_CREATED)
        policy = Policy.objects.get(code="POL-001")

        action_plan_response = self.client.post(
            "/api/action-plans/",
            {
                "organization": str(self.organization.uuid),
                "risk": str(risk.uuid),
                "control": str(control.uuid),
                "policy": str(policy.uuid),
                "title": "Reduce contract exposure risk",
                "description": "Define controls for contract analysis.",
                "status": ActionPlan.Status.OPEN,
                "owner_membership": str(membership.uuid),
            },
            format="json",
        )

        self.assertEqual(action_plan_response.status_code, status.HTTP_201_CREATED)
        action_plan = ActionPlan.objects.get(title="Reduce contract exposure risk")

        action_item_response = self.client.post(
            "/api/action-items/",
            {
                "organization": str(self.organization.uuid),
                "action_plan": str(action_plan.uuid),
                "risk": str(risk.uuid),
                "control": str(control.uuid),
                "title": "Review access permissions",
                "description": "Confirm least privilege.",
                "status": ActionItem.Status.TODO,
                "owner_membership": str(membership.uuid),
            },
            format="json",
        )

        self.assertEqual(action_item_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(RiskAssessment.objects.filter(risk=risk).exists())
        self.assertTrue(ActionItem.objects.filter(title="Review access permissions").exists())
        self.assertTrue(AuditEvent.objects.filter(event_type="risk_assessment.created").exists())
        self.assertTrue(AuditEvent.objects.filter(event_type="policy.created").exists())
        self.assertTrue(AuditEvent.objects.filter(event_type="action_plan.created").exists())
        self.assertTrue(AuditEvent.objects.filter(event_type="action_item.created").exists())

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

    def test_create_action_plan_rejects_cross_tenant_risk(self):
        hidden_org = Organization.objects.create(name="Hidden Corp", slug="hidden-corp")
        hidden_risk = Risk.objects.create(
            organization=hidden_org,
            title="Hidden risk",
            likelihood=2,
            impact=3,
            severity=RiskLevel.MEDIUM,
        )

        response = self.client.post(
            "/api/action-plans/",
            {
                "organization": str(self.organization.uuid),
                "risk": str(hidden_risk.uuid),
                "title": "Cross tenant plan",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
