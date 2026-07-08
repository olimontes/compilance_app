from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.organizations.models import Organization

from .models import (
    Assessment,
    AssessmentAnswer,
    AssessmentDimension,
    AssessmentFramework,
    AssessmentQuestion,
)


class AssessmentModelTests(TestCase):
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
        self.framework = AssessmentFramework.objects.create(
            code="AIGOV",
            name="AI Governance Maturity",
            version="1.0",
            status=AssessmentFramework.Status.PUBLISHED,
        )
        self.dimension = AssessmentDimension.objects.create(
            framework=self.framework,
            code="privacy",
            name="Privacy",
            display_order=1,
        )
        self.question = AssessmentQuestion.objects.create(
            framework=self.framework,
            dimension=self.dimension,
            code="privacy-001",
            text="Does the organization classify personal data in AI systems?",
            answer_type=AssessmentQuestion.AnswerType.BOOLEAN,
            weight=2,
        )

    def test_create_assessment_answer(self):
        assessment = Assessment.objects.create(
            organization=self.organization,
            framework=self.framework,
            created_by=self.user,
            title="2026 AI governance assessment",
        )
        answer = AssessmentAnswer.objects.create(
            assessment=assessment,
            question=self.question,
            answered_by=self.user,
            value={"answer": True},
            score=2,
            notes="Data classification is documented.",
        )

        self.assertEqual(answer.assessment, assessment)
        self.assertEqual(answer.question, self.question)
        self.assertEqual(assessment.framework, self.framework)
        self.assertTrue(answer.uuid)

    def test_framework_code_version_is_unique(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            AssessmentFramework.objects.create(
                code="AIGOV",
                name="Duplicate",
                version="1.0",
            )

    def test_answer_is_unique_per_assessment_and_question(self):
        assessment = Assessment.objects.create(
            organization=self.organization,
            framework=self.framework,
            created_by=self.user,
            title="2026 AI governance assessment",
        )
        AssessmentAnswer.objects.create(
            assessment=assessment,
            question=self.question,
            answered_by=self.user,
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            AssessmentAnswer.objects.create(
                assessment=assessment,
                question=self.question,
                answered_by=self.user,
            )
