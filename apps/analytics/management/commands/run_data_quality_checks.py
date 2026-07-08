from django.core.management.base import BaseCommand
from django.db import transaction

from apps.analytics.models import DataQualityCheck
from apps.analytics.services import run_data_quality_checks


class Command(BaseCommand):
    help = "Run baseline data quality checks and store their results."

    @transaction.atomic
    def handle(self, *args, **options):
        checks = run_data_quality_checks()
        failed = sum(1 for check in checks if check.status == DataQualityCheck.Status.FAILED)
        self.stdout.write(
            self.style.SUCCESS(
                f"Ran {len(checks)} data quality checks: {failed} failed."
            )
        )
