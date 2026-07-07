from django.conf import settings
from django.db import models

from apps.assessments.models import AssessmentAnswer
from apps.common.models import TimestampedUUIDModel
from apps.compliance.models import Control, Risk
from apps.organizations.models import Organization


class Evidence(TimestampedUUIDModel):
    class EvidenceType(models.TextChoices):
        DOCUMENT = "document", "Document"
        LINK = "link", "Link"
        SCREENSHOT = "screenshot", "Screenshot"
        REPORT = "report", "Report"
        OTHER = "other", "Other"

    class StorageBackend(models.TextChoices):
        EXTERNAL_URL = "external_url", "External URL"
        LOCAL = "local", "Local"
        S3 = "s3", "S3"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        PENDING_REVIEW = "pending_review", "Pending review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        ARCHIVED = "archived", "Archived"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="evidence",
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="uploaded_evidence",
        blank=True,
        null=True,
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    evidence_type = models.CharField(
        max_length=50,
        choices=EvidenceType.choices,
        default=EvidenceType.LINK,
    )
    storage_backend = models.CharField(
        max_length=50,
        choices=StorageBackend.choices,
        default=StorageBackend.EXTERNAL_URL,
    )
    file_path = models.CharField(max_length=500, blank=True)
    external_url = models.URLField(max_length=500, blank=True)
    checksum = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    class Meta:
        ordering = ["organization__name", "-created_at"]

    def __str__(self) -> str:
        return self.title


class EvidenceLink(models.Model):
    evidence = models.ForeignKey(
        Evidence,
        on_delete=models.CASCADE,
        related_name="links",
    )
    risk = models.ForeignKey(
        Risk,
        on_delete=models.CASCADE,
        related_name="evidence_links",
        blank=True,
        null=True,
    )
    control = models.ForeignKey(
        Control,
        on_delete=models.CASCADE,
        related_name="evidence_links",
        blank=True,
        null=True,
    )
    assessment_answer = models.ForeignKey(
        AssessmentAnswer,
        on_delete=models.CASCADE,
        related_name="evidence_links",
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["evidence__title", "-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(risk__isnull=False, control__isnull=True, assessment_answer__isnull=True)
                    | models.Q(risk__isnull=True, control__isnull=False, assessment_answer__isnull=True)
                    | models.Q(risk__isnull=True, control__isnull=True, assessment_answer__isnull=False)
                ),
                name="evidence_link_has_exactly_one_target",
            )
        ]

    def __str__(self) -> str:
        return f"{self.evidence} link"

