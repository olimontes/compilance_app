from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from apps.ai_assets.models import RiskLevel
from apps.compliance.models import Risk
from apps.evidence.models import Evidence
from apps.organizations.models import Organization

from .models import DataQualityCheck


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
