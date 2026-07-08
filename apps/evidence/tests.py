from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.ai_assets.models import RiskLevel
from apps.assessments.models import (
    Assessment,
    AssessmentAnswer,
    AssessmentDimension,
    AssessmentFramework,
    AssessmentQuestion,
)
from apps.compliance.models import Control, Risk
from apps.organizations.models import Organization

from .models import Evidence, EvidenceLink


class EvidenceModelTests(TestCase):
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
        self.risk = Risk.objects.create(
            organization=self.organization,
            title="Confidential information exposure",
            likelihood=3,
            impact=4,
            severity=RiskLevel.HIGH,
        )
        self.control = Control.objects.create(
            organization=self.organization,
            code="CTRL-001",
            title="Access review",
        )
        framework = AssessmentFramework.objects.create(
            code="AIGOV",
            name="AI Governance Maturity",
            version="1.0",
        )
        dimension = AssessmentDimension.objects.create(
            framework=framework,
            code="privacy",
            name="Privacy",
        )
        question = AssessmentQuestion.objects.create(
            framework=framework,
            dimension=dimension,
            code="privacy-001",
            text="Does the organization classify personal data in AI systems?",
            answer_type=AssessmentQuestion.AnswerType.BOOLEAN,
        )
        assessment = Assessment.objects.create(
            organization=self.organization,
            framework=framework,
            created_by=self.user,
            title="2026 AI governance assessment",
        )
        self.answer = AssessmentAnswer.objects.create(
            assessment=assessment,
            question=question,
            answered_by=self.user,
        )

    def test_create_evidence_links(self):
        evidence = Evidence.objects.create(
            organization=self.organization,
            uploaded_by=self.user,
            title="Access policy",
            external_url="https://example.com/access-policy",
        )

        risk_link = EvidenceLink.objects.create(evidence=evidence, risk=self.risk)
        control_link = EvidenceLink.objects.create(evidence=evidence, control=self.control)
        answer_link = EvidenceLink.objects.create(
            evidence=evidence,
            assessment_answer=self.answer,
        )

        self.assertEqual(risk_link.risk, self.risk)
        self.assertEqual(control_link.control, self.control)
        self.assertEqual(answer_link.assessment_answer, self.answer)
        self.assertEqual(evidence.links.count(), 3)

    def test_evidence_link_requires_exactly_one_target(self):
        evidence = Evidence.objects.create(
            organization=self.organization,
            title="Access policy",
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            EvidenceLink.objects.create(evidence=evidence)

        with self.assertRaises(IntegrityError), transaction.atomic():
            EvidenceLink.objects.create(
                evidence=evidence,
                risk=self.risk,
                control=self.control,
            )
