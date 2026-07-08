from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.organizations.models import Membership, Organization

from .models import DataQualityCheck, IngestionRun, MetricDefinition, MetricSnapshot


class AnalyticsApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="alice",
            email="alice@example.com",
            password="password-123",
        )
        self.organization = Organization.objects.create(name="Acme Corp", slug="acme-corp")
        Membership.objects.create(user=self.user, organization=self.organization)
        self.metric = MetricDefinition.objects.create(
            key="risks.high.count",
            name="High risks",
            value_type=MetricDefinition.ValueType.INTEGER,
        )
        self.client.force_authenticate(self.user)

    def test_create_metric_snapshot(self):
        now = timezone.now()

        response = self.client.post(
            "/api/metric-snapshots/",
            {
                "organization": str(self.organization.uuid),
                "metric_definition": str(self.metric.uuid),
                "metric_value": "3.0000",
                "dimensions": {"severity": "high"},
                "period_start": now.isoformat(),
                "period_end": now.isoformat(),
                "computed_at": now.isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(MetricSnapshot.objects.filter(metric_value=3).exists())

    def test_list_metric_snapshots_only_returns_user_organizations(self):
        hidden_org = Organization.objects.create(name="Hidden Corp", slug="hidden-corp")
        now = timezone.now()
        visible_snapshot = MetricSnapshot.objects.create(
            organization=self.organization,
            metric_definition=self.metric,
            metric_value=3,
            period_start=now,
            period_end=now,
            computed_at=now,
        )
        MetricSnapshot.objects.create(
            organization=hidden_org,
            metric_definition=self.metric,
            metric_value=7,
            period_start=now,
            period_end=now,
            computed_at=now,
        )

        response = self.client.get("/api/metric-snapshots/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        values = {item["metric_value"] for item in response.json()["results"]}
        self.assertIn(f"{visible_snapshot.metric_value:.4f}", values)
        self.assertNotIn("7.0000", values)

    def test_create_quality_check_and_ingestion_run(self):
        now = timezone.now()
        quality_response = self.client.post(
            "/api/data-quality-checks/",
            {
                "check_key": "risk.severity.valid",
                "target_table": "compliance_risk",
                "status": DataQualityCheck.Status.PASSED,
                "result": {"invalid_rows": 0},
                "executed_at": now.isoformat(),
            },
            format="json",
        )
        ingestion_response = self.client.post(
            "/api/ingestion-runs/",
            {
                "source_name": "manual_csv",
                "status": IngestionRun.Status.SUCCESS,
                "started_at": now.isoformat(),
                "finished_at": now.isoformat(),
                "rows_read": 10,
                "rows_written": 10,
            },
            format="json",
        )

        self.assertEqual(quality_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ingestion_response.status_code, status.HTTP_201_CREATED)

    def test_create_metric_snapshot_rejects_non_member_organization(self):
        hidden_org = Organization.objects.create(name="Hidden Corp", slug="hidden-corp")
        now = timezone.now()

        response = self.client.post(
            "/api/metric-snapshots/",
            {
                "organization": str(hidden_org.uuid),
                "metric_definition": str(self.metric.uuid),
                "metric_value": "3.0000",
                "period_start": now.isoformat(),
                "period_end": now.isoformat(),
                "computed_at": now.isoformat(),
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
