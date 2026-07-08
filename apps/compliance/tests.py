from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.ai_assets.models import AiTool, AiUseCase, RiskLevel
from apps.organizations.models import Organization

from .models import Control, Risk, RiskControl


class ComplianceModelTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Acme Corp",
            slug="acme-corp",
        )
        self.tool = AiTool.objects.create(
            organization=self.organization,
            name="Contract Assistant",
        )
        self.use_case = AiUseCase.objects.create(
            organization=self.organization,
            ai_tool=self.tool,
            name="Contract review",
            purpose="Support first-pass contract analysis.",
            risk_level=RiskLevel.HIGH,
        )

    def test_create_risk_control_link(self):
        risk = Risk.objects.create(
            organization=self.organization,
            ai_use_case=self.use_case,
            title="Confidential information exposure",
            description="Contracts may include confidential clauses.",
            likelihood=3,
            impact=4,
            severity=RiskLevel.HIGH,
        )
        control = Control.objects.create(
            organization=self.organization,
            code="CTRL-001",
            title="Access review",
            domain="security",
        )
        link = RiskControl.objects.create(risk=risk, control=control)

        self.assertEqual(link.risk, risk)
        self.assertEqual(link.control, control)
        self.assertIn(control, risk.controls.all())

    def test_control_code_is_unique_per_organization(self):
        Control.objects.create(
            organization=self.organization,
            code="CTRL-001",
            title="Access review",
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            Control.objects.create(
                organization=self.organization,
                code="CTRL-001",
                title="Duplicate access review",
            )

    def test_risk_control_pair_is_unique(self):
        risk = Risk.objects.create(
            organization=self.organization,
            ai_use_case=self.use_case,
            title="Confidential information exposure",
            likelihood=3,
            impact=4,
            severity=RiskLevel.HIGH,
        )
        control = Control.objects.create(
            organization=self.organization,
            code="CTRL-001",
            title="Access review",
        )
        RiskControl.objects.create(risk=risk, control=control)

        with self.assertRaises(IntegrityError), transaction.atomic():
            RiskControl.objects.create(risk=risk, control=control)
