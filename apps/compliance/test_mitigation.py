from django.contrib.auth import get_user_model
from django.core.management import call_command
from rest_framework import status
from rest_framework.test import APITestCase

from apps.assessments.models import Assessment, AssessmentAnswer, AssessmentFramework, AssessmentQuestion
from apps.organizations.models import Membership, Organization

from .models import ActionItem, ActionPlan, Risk, RiskControl


class MitigationPlanApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="alice",
            email="alice@example.com",
            password="password-123",
        )
        self.organization = Organization.objects.create(name="Acme Corp", slug="acme-corp")
        Membership.objects.create(user=self.user, organization=self.organization)
        call_command("seed_assessment_frameworks", verbosity=0)
        call_command("seed_controls", organization_slug=self.organization.slug, verbosity=0)
        self.framework = AssessmentFramework.objects.get(code="AIGOV", version="1.0")
        self.client.force_authenticate(self.user)

    def test_generate_mitigation_plan_from_submitted_assessment(self):
        assessment = self._submitted_assessment(false_question_codes={"data-sharing-001", "security-001"})

        response = self.client.post(
            f"/api/assessments/{assessment.uuid}/generate-mitigation-plan/",
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload["generated_count"], 2)
        self.assertEqual(Risk.objects.filter(organization=self.organization).count(), 2)
        self.assertTrue(ActionPlan.objects.filter(organization=self.organization).exists())
        self.assertTrue(ActionItem.objects.filter(organization=self.organization).exists())
        self.assertTrue(RiskControl.objects.filter(risk__organization=self.organization).exists())

    def test_generate_mitigation_plan_is_idempotent(self):
        assessment = self._submitted_assessment(false_question_codes={"security-001"})

        first_response = self.client.post(
            f"/api/assessments/{assessment.uuid}/generate-mitigation-plan/",
            format="json",
        )
        counts_after_first_run = (
            Risk.objects.count(),
            ActionPlan.objects.count(),
            ActionItem.objects.count(),
            RiskControl.objects.count(),
        )
        second_response = self.client.post(
            f"/api/assessments/{assessment.uuid}/generate-mitigation-plan/",
            format="json",
        )

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            counts_after_first_run,
            (
                Risk.objects.count(),
                ActionPlan.objects.count(),
                ActionItem.objects.count(),
                RiskControl.objects.count(),
            ),
        )

    def test_generate_mitigation_plan_requires_submitted_assessment(self):
        assessment = Assessment.objects.create(
            organization=self.organization,
            framework=self.framework,
            created_by=self.user,
            title="Draft AI governance assessment",
        )

        response = self.client.post(
            f"/api/assessments/{assessment.uuid}/generate-mitigation-plan/",
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("assessment", response.json())

    def _submitted_assessment(self, false_question_codes):
        assessment = Assessment.objects.create(
            organization=self.organization,
            framework=self.framework,
            created_by=self.user,
            title="2026 AI governance assessment",
        )
        for question in AssessmentQuestion.objects.filter(framework=self.framework):
            if not question.is_required:
                continue
            value = self._answer_value(question, false_question_codes)
            AssessmentAnswer.objects.create(
                assessment=assessment,
                question=question,
                answered_by=self.user,
                value=value,
            )
        submit_response = self.client.post(f"/api/assessments/{assessment.uuid}/submit/", format="json")
        self.assertEqual(submit_response.status_code, status.HTTP_200_OK)
        assessment.refresh_from_db()
        return assessment

    def _answer_value(self, question, false_question_codes):
        if question.answer_type == AssessmentQuestion.AnswerType.TEXT:
            return {"text": f"Detailed answer for {question.code}."}
        return {"answer": question.code not in false_question_codes}
