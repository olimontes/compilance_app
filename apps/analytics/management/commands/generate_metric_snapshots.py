from django.core.management.base import BaseCommand
from django.db import transaction

from apps.analytics.services import generate_metric_snapshots


class Command(BaseCommand):
    help = "Generate metric snapshots from transactional data."

    @transaction.atomic
    def handle(self, *args, **options):
        snapshots = generate_metric_snapshots()
        self.stdout.write(
            self.style.SUCCESS(
                f"Generated {len(snapshots)} metric snapshots."
            )
        )
