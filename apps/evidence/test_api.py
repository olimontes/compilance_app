from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.ai_assets.models import RiskLevel
from apps.audit.models import AuditEvent
from apps.compliance.models import Control, Risk
from apps.organizations.models import Membership, Organization

from .models import Evidence, EvidenceLink, EvidenceReview


class EvidenceApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="alice",
            email="alice@example.com",
            password="password-123",
        )
        self.organization = Organization.objects.create(name="Acme Corp", slug="acme-corp")
        Membership.objects.create(user=self.user, organization=self.organization)
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
        self.client.force_authenticate(self.user)

    def test_create_evidence(self):
        response = self.client.post(
            "/api/evidence/",
            {
                "organization": str(self.organization.uuid),
                "title": "Access policy",
                "description": "Access policy stored externally.",
                "evidence_type": Evidence.EvidenceType.LINK,
                "storage_backend": Evidence.StorageBackend.EXTERNAL_URL,
                "external_url": "https://example.com/access-policy",
                "status": Evidence.Status.ACTIVE,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        evidence = Evidence.objects.get(title="Access policy")
        self.assertEqual(evidence.uploaded_by, self.user)
        self.assertTrue(AuditEvent.objects.filter(event_type="evidence.uploaded").exists())

    def test_create_evidence_link_to_risk(self):
        evidence = Evidence.objects.create(
            organization=self.organization,
            uploaded_by=self.user,
            title="Access policy",
        )

        response = self.client.post(
            "/api/evidence-links/",
            {
                "evidence": str(evidence.uuid),
                "risk": str(self.risk.uuid),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(EvidenceLink.objects.filter(evidence=evidence, risk=self.risk).exists())

    def test_create_evidence_review(self):
        evidence = Evidence.objects.create(
            organization=self.organization,
            uploaded_by=self.user,
            title="Access policy",
        )

        response = self.client.post(
            "/api/evidence-reviews/",
            {
                "evidence": str(evidence.uuid),
                "status": EvidenceReview.Status.APPROVED,
                "comments": "Evidence is valid for this control.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        review = EvidenceReview.objects.get(evidence=evidence)
        self.assertEqual(review.reviewed_by, self.user)
        self.assertTrue(AuditEvent.objects.filter(event_type="evidence_review.created").exists())

    def test_evidence_link_rejects_multiple_targets(self):
        evidence = Evidence.objects.create(
            organization=self.organization,
            uploaded_by=self.user,
            title="Access policy",
        )

        response = self.client.post(
            "/api/evidence-links/",
            {
                "evidence": str(evidence.uuid),
                "risk": str(self.risk.uuid),
                "control": str(self.control.uuid),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_evidence_only_returns_user_organizations(self):
        hidden_org = Organization.objects.create(name="Hidden Corp", slug="hidden-corp")
        visible_evidence = Evidence.objects.create(
            organization=self.organization,
            title="Visible evidence",
        )
        Evidence.objects.create(organization=hidden_org, title="Hidden evidence")

        response = self.client.get("/api/evidence/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        titles = {item["title"] for item in response.json()["results"]}
        self.assertIn(visible_evidence.title, titles)
        self.assertNotIn("Hidden evidence", titles)

    def test_evidence_link_rejects_target_from_another_organization(self):
        hidden_org = Organization.objects.create(name="Hidden Corp", slug="hidden-corp")
        hidden_risk = Risk.objects.create(
            organization=hidden_org,
            title="Hidden risk",
            likelihood=3,
            impact=4,
            severity=RiskLevel.HIGH,
        )
        evidence = Evidence.objects.create(
            organization=self.organization,
            uploaded_by=self.user,
            title="Access policy",
        )

        response = self.client.post(
            "/api/evidence-links/",
            {
                "evidence": str(evidence.uuid),
                "risk": str(hidden_risk.uuid),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_evidence_review_rejects_other_organization(self):
        hidden_org = Organization.objects.create(name="Hidden Corp", slug="hidden-corp")
        hidden_evidence = Evidence.objects.create(organization=hidden_org, title="Hidden evidence")

        response = self.client.post(
            "/api/evidence-reviews/",
            {
                "evidence": str(hidden_evidence.uuid),
                "status": EvidenceReview.Status.APPROVED,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
