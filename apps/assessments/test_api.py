from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.audit.models import AuditEvent
from apps.organizations.models import Membership, Organization

from .models import (
    Assessment,
    AssessmentAnswer,
    AssessmentDimension,
    AssessmentFramework,
    AssessmentQuestion,
    MaturityScore,
    Recommendation,
)


class AssessmentApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="alice",
            email="alice@example.com",
            password="password-123",
        )
        self.organization = Organization.objects.create(name="Acme Corp", slug="acme-corp")
        Membership.objects.create(user=self.user, organization=self.organization)
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
        )
        self.question = AssessmentQuestion.objects.create(
            framework=self.framework,
            dimension=self.dimension,
            code="privacy-001",
            text="Does the organization classify personal data in AI systems?",
            answer_type=AssessmentQuestion.AnswerType.BOOLEAN,
        )
        self.client.force_authenticate(self.user)

    def test_create_assessment(self):
        response = self.client.post(
            "/api/assessments/",
            {
                "organization": str(self.organization.uuid),
                "framework": str(self.framework.uuid),
                "title": "2026 AI governance assessment",
                "status": Assessment.Status.DRAFT,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        assessment = Assessment.objects.get(title="2026 AI governance assessment")
        self.assertEqual(assessment.created_by, self.user)
        self.assertTrue(AuditEvent.objects.filter(event_type="assessment.started").exists())

    def test_create_assessment_answer(self):
        assessment = Assessment.objects.create(
            organization=self.organization,
            framework=self.framework,
            created_by=self.user,
            title="2026 AI governance assessment",
        )

        response = self.client.post(
            "/api/assessment-answers/",
            {
                "assessment": str(assessment.uuid),
                "question": str(self.question.uuid),
                "value": {"answer": True},
                "score": "1.00",
                "notes": "Documented.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        answer = AssessmentAnswer.objects.get(assessment=assessment, question=self.question)
        self.assertEqual(answer.answered_by, self.user)
        self.assertTrue(AuditEvent.objects.filter(event_type="assessment_answer.created").exists())

    def test_create_maturity_score_and_recommendation(self):
        assessment = Assessment.objects.create(
            organization=self.organization,
            framework=self.framework,
            created_by=self.user,
            title="2026 AI governance assessment",
        )

        score_response = self.client.post(
            "/api/maturity-scores/",
            {
                "assessment": str(assessment.uuid),
                "dimension": str(self.dimension.uuid),
                "score": "7.00",
                "max_score": "10.00",
                "percentage": "70.00",
                "computed_at": timezone.now().isoformat(),
            },
            format="json",
        )

        self.assertEqual(score_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(MaturityScore.objects.filter(assessment=assessment, dimension=self.dimension).exists())

        recommendation_response = self.client.post(
            "/api/recommendations/",
            {
                "assessment": str(assessment.uuid),
                "dimension": str(self.dimension.uuid),
                "title": "Improve privacy classification",
                "description": "Document data classification for AI use cases.",
                "priority": Recommendation.Priority.HIGH,
                "status": Recommendation.Status.OPEN,
            },
            format="json",
        )

        self.assertEqual(recommendation_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Recommendation.objects.filter(title="Improve privacy classification").exists())
        self.assertTrue(AuditEvent.objects.filter(event_type="maturity_score.created").exists())
        self.assertTrue(AuditEvent.objects.filter(event_type="recommendation.created").exists())

    def test_list_assessments_only_returns_user_organizations(self):
        visible = Assessment.objects.create(
            organization=self.organization,
            framework=self.framework,
            created_by=self.user,
            title="Visible assessment",
        )
        hidden_org = Organization.objects.create(name="Hidden Corp", slug="hidden-corp")
        Assessment.objects.create(
            organization=hidden_org,
            framework=self.framework,
            created_by=self.user,
            title="Hidden assessment",
        )

        response = self.client.get("/api/assessments/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = {item["title"] for item in response.json()["results"]}
        self.assertIn(visible.title, titles)
        self.assertNotIn("Hidden assessment", titles)

    def test_create_assessment_rejects_non_member_organization(self):
        hidden_org = Organization.objects.create(name="Hidden Corp", slug="hidden-corp")

        response = self.client.post(
            "/api/assessments/",
            {
                "organization": str(hidden_org.uuid),
                "framework": str(self.framework.uuid),
                "title": "Cross tenant assessment",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_recommendation_rejects_dimension_from_other_framework(self):
        other_framework = AssessmentFramework.objects.create(
            code="OTHER",
            name="Other Framework",
            version="1.0",
        )
        other_dimension = AssessmentDimension.objects.create(
            framework=other_framework,
            code="other",
            name="Other",
        )
        assessment = Assessment.objects.create(
            organization=self.organization,
            framework=self.framework,
            created_by=self.user,
            title="2026 AI governance assessment",
        )

        response = self.client.post(
            "/api/recommendations/",
            {
                "assessment": str(assessment.uuid),
                "dimension": str(other_dimension.uuid),
                "title": "Invalid recommendation",
                "description": "Wrong framework dimension.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
