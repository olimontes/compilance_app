from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.compliance.models import Control
from apps.organizations.models import Organization


CONTROLS = [
    {
        "code": "GOV-001",
        "title": "AI inventory ownership",
        "description": "Maintain an owner for each AI tool and AI use case registered by the organization.",
        "domain": "governance",
    },
    {
        "code": "GOV-002",
        "title": "AI use case approval",
        "description": "Require approval before moving AI use cases to production.",
        "domain": "governance",
    },
    {
        "code": "PRIV-001",
        "title": "Data classification review",
        "description": "Classify data sensitivity for AI use cases before production use.",
        "domain": "privacy",
    },
    {
        "code": "SEC-001",
        "title": "Access control review",
        "description": "Review access to AI tools and related evidence repositories periodically.",
        "domain": "security",
    },
    {
        "code": "HUM-001",
        "title": "Mandatory human review",
        "description": "Require human validation before using AI outputs in relevant decisions or critical processes.",
        "domain": "human_review",
    },
    {
        "code": "TRN-001",
        "title": "AI governance training",
        "description": "Train users on acceptable, secure, and responsible AI usage.",
        "domain": "governance",
    },
    {
        "code": "OPS-001",
        "title": "AI continuity fallback",
        "description": "Define fallback procedures for critical processes that depend on AI tools.",
        "domain": "operations",
    },
    {
        "code": "EVD-001",
        "title": "Evidence retention",
        "description": "Keep evidence links or documents for relevant risks, controls, and assessment answers.",
        "domain": "evidence",
    },
]


class Command(BaseCommand):
    help = "Seed baseline controls for an organization."

    def add_arguments(self, parser):
        parser.add_argument(
            "--organization-slug",
            required=True,
            help="Slug of the organization that will receive the baseline controls.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        organization_slug = options["organization_slug"]
        try:
            organization = Organization.objects.get(slug=organization_slug)
        except Organization.DoesNotExist as exc:
            raise CommandError(f'Organization with slug "{organization_slug}" was not found.') from exc

        for control_data in CONTROLS:
            Control.objects.update_or_create(
                organization=organization,
                code=control_data["code"],
                defaults={
                    **control_data,
                    "status": Control.Status.ACTIVE,
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(CONTROLS)} controls for organization {organization.slug}."
            )
        )
