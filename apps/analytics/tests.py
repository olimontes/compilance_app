from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from apps.organizations.models import Organization

from .models import DataQualityCheck, IngestionRun, MetricDefinition, MetricSnapshot


class AnalyticsModelTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Acme Corp",
            slug="acme-corp",
        )
        self.metric = MetricDefinition.objects.create(
            key="risks.high.count",
            name="High risks",
            value_type=MetricDefinition.ValueType.INTEGER,
        )

    def test_create_metric_snapshot(self):
        now = timezone.now()
        snapshot = MetricSnapshot.objects.create(
            organization=self.organization,
            metric_definition=self.metric,
            metric_value=3,
            dimensions={"severity": "high"},
            period_start=now,
            period_end=now,
            computed_at=now,
        )

        self.assertEqual(snapshot.organization, self.organization)
        self.assertEqual(snapshot.metric_definition, self.metric)
        self.assertEqual(snapshot.dimensions["severity"], "high")

    def test_metric_snapshot_is_unique_per_period(self):
        now = timezone.now()
        MetricSnapshot.objects.create(
            organization=self.organization,
            metric_definition=self.metric,
            metric_value=3,
            period_start=now,
            period_end=now,
            computed_at=now,
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            MetricSnapshot.objects.create(
                organization=self.organization,
                metric_definition=self.metric,
                metric_value=4,
                period_start=now,
                period_end=now,
                computed_at=now,
            )

    def test_create_data_quality_check_and_ingestion_run(self):
        now = timezone.now()
        check = DataQualityCheck.objects.create(
            check_key="risk.severity.valid",
            target_table="compliance_risk",
            status=DataQualityCheck.Status.PASSED,
            result={"invalid_rows": 0},
            executed_at=now,
        )
        run = IngestionRun.objects.create(
            source_name="manual_csv",
            status=IngestionRun.Status.SUCCESS,
            started_at=now,
            finished_at=now,
            rows_read=10,
            rows_written=10,
        )

        self.assertEqual(check.result["invalid_rows"], 0)
        self.assertEqual(run.rows_written, 10)

