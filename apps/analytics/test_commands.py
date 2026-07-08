from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from apps.ai_assets.models import AiUseCase, RiskLevel
from apps.assessments.models import Assessment, AssessmentFramework
from apps.compliance.models import Control, Risk
from apps.evidence.models import Evidence
from apps.organizations.models import Organization

from .models import DataQualityCheck, MetricDefinition, MetricSnapshot


class DataQualityCommandTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Acme Corp", slug="acme-corp")

    def test_run_data_quality_checks_records_results(self):
        output = StringIO()

        call_command("run_data_quality_checks", stdout=output)

        self.assertEqual(DataQualityCheck.objects.count(), 5)
        self.assertIn("Ran 5 data quality checks", output.getvalue())
        self.assertTrue(
            DataQualityCheck.objects.filter(
                check_key="evidence.location.present",
                status=DataQualityCheck.Status.PASSED,
            ).exists()
        )

    def test_run_data_quality_checks_marks_failures(self):
        Evidence.objects.create(
            organization=self.organization,
            title="Missing location evidence",
        )
        Risk.objects.create(
            organization=self.organization,
            title="Out of range risk",
            likelihood=6,
            impact=0,
            severity=RiskLevel.HIGH,
        )

        call_command("run_data_quality_checks", stdout=StringIO())

        evidence_check = DataQualityCheck.objects.get(check_key="evidence.location.present")
        risk_check = DataQualityCheck.objects.get(check_key="risk.scale.valid")
        self.assertEqual(evidence_check.status, DataQualityCheck.Status.FAILED)
        self.assertEqual(evidence_check.result["invalid_rows"], 1)
        self.assertEqual(risk_check.status, DataQualityCheck.Status.FAILED)
        self.assertEqual(risk_check.result["invalid_rows"], 2)


class MetricSnapshotCommandTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Acme Corp", slug="acme-corp")
        self.framework = AssessmentFramework.objects.create(
            code="AIGOV",
            name="AI Governance",
            version="1.0",
        )

    def test_generate_metric_snapshots_records_counts(self):
        user = get_user_model().objects.create_user(
            username="alice",
            email="alice@example.com",
            password="password-123",
        )
        AiUseCase.objects.create(
            organization=self.organization,
            name="Contract review",
            purpose="Support contract analysis.",
        )
        Control.objects.create(
            organization=self.organization,
            code="CTRL-001",
            title="Access review",
        )
        Evidence.objects.create(
            organization=self.organization,
            title="Access policy",
            external_url="https://example.com/access-policy",
        )
        Risk.objects.create(
            organization=self.organization,
            title="High risk",
            likelihood=3,
            impact=4,
            severity=RiskLevel.HIGH,
        )
        Assessment.objects.create(
            organization=self.organization,
            framework=self.framework,
            created_by=user,
            title="Assessment",
            status=Assessment.Status.IN_PROGRESS,
        )

        output = StringIO()
        call_command("generate_metric_snapshots", stdout=output)

        self.assertIn("Generated 15 metric snapshots", output.getvalue())
        self.assertEqual(MetricDefinition.objects.count(), 15)
        self.assertEqual(MetricSnapshot.objects.count(), 15)
        high_risks = MetricSnapshot.objects.get(metric_definition__key="risks.high.count")
        in_progress_assessments = MetricSnapshot.objects.get(
            metric_definition__key="assessments.in_progress.count"
        )
        self.assertEqual(high_risks.metric_value, 1)
        self.assertEqual(in_progress_assessments.metric_value, 1)

    def test_generate_metric_snapshots_is_idempotent_for_same_period(self):
        now = timezone.now()
        from apps.analytics.services import generate_metric_snapshots

        generate_metric_snapshots(computed_at=now)
        generate_metric_snapshots(computed_at=now.replace(hour=23, minute=30))

        self.assertEqual(MetricSnapshot.objects.count(), 15)
