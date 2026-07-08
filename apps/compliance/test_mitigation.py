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

    def test_generate_mitigation_plan_returns_enriched_execution_fields(self):
        assessment = self._submitted_assessment(false_question_codes={"data-sharing-001"})

        response = self.client.post(
            f"/api/assessments/{assessment.uuid}/generate-mitigation-plan/",
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload["generated_count"], 1)
        item = payload["items"][0]
        self.assertEqual(item["risk"]["dimension"]["code"], "data-sharing")
        self.assertEqual(
            set(item["risk"]["consequences"]),
            {"legal", "financial", "operational", "reputational"},
        )
        self.assertTrue(item["action_plan"]["success_indicators"])
        self.assertTrue(item["action_plan"]["expected_evidence"])
        self.assertTrue(item["action_plan"]["expected_benefits"])
        self.assertEqual(item["action_plan"]["complexity"], "high")
        self.assertTrue(item["action_items"][0]["success_indicators"])
        self.assertTrue(item["action_items"][0]["expected_evidence"])

        stored_item = ActionItem.objects.get(uuid=item["action_items"][0]["uuid"])
        self.assertIn("Success indicators:", stored_item.description)
        self.assertIn("Expected evidence:", stored_item.description)
        self.assertEqual(stored_item.due_date.isoformat(), item["action_items"][0]["due_date"])

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

    def test_executive_report_returns_risks_consequences_and_plan(self):
        assessment = self._submitted_assessment(false_question_codes={"data-sharing-001", "security-001"})
        mitigation_response = self.client.post(
            f"/api/assessments/{assessment.uuid}/generate-mitigation-plan/",
            format="json",
        )

        response = self.client.get(f"/api/assessments/{assessment.uuid}/executive-report/")

        self.assertEqual(mitigation_response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload["assessment"]["uuid"], str(assessment.uuid))
        self.assertEqual(payload["executive_summary"]["identified_risk_count"], 2)
        self.assertEqual(payload["executive_summary"]["priority_risk_count"], 2)
        self.assertTrue(payload["executive_summary"]["recommended_focus"])

        risks_by_dimension = {
            item["dimension"]["code"]: item
            for item in payload["identified_risks"]
        }
        self.assertIn("data-sharing", risks_by_dimension)
        self.assertEqual(
            set(risks_by_dimension["data-sharing"]["consequences"]),
            {"legal", "financial", "operational", "reputational"},
        )

        plans_by_dimension = {
            item["dimension"]["code"]: item
            for item in payload["mitigation_plan"]
        }
        data_sharing_plan = plans_by_dimension["data-sharing"]
        self.assertEqual(data_sharing_plan["status"], ActionPlan.Status.OPEN)
        self.assertTrue(data_sharing_plan["objective"])
        self.assertTrue(data_sharing_plan["success_indicators"])
        self.assertTrue(data_sharing_plan["expected_evidence"])
        self.assertTrue(data_sharing_plan["items"])

    def test_executive_report_requires_submitted_assessment(self):
        assessment = Assessment.objects.create(
            organization=self.organization,
            framework=self.framework,
            created_by=self.user,
            title="Draft AI governance assessment",
        )

        response = self.client.get(f"/api/assessments/{assessment.uuid}/executive-report/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("assessment", response.json())

    def test_executive_report_respects_organization_scope(self):
        hidden_organization = Organization.objects.create(name="Hidden Corp", slug="hidden-corp")
        hidden_assessment = Assessment.objects.create(
            organization=hidden_organization,
            framework=self.framework,
            created_by=self.user,
            title="Hidden AI governance assessment",
        )

        response = self.client.get(f"/api/assessments/{hidden_assessment.uuid}/executive-report/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

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
