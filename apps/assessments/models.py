from django.conf import settings
from django.db import models

from apps.common.models import TimestampedUUIDModel
from apps.organizations.models import Organization


class AssessmentFramework(TimestampedUUIDModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        RETIRED = "retired", "Retired"

    code = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=50)
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    class Meta:
        ordering = ["code", "version"]
        constraints = [
            models.UniqueConstraint(
                fields=["code", "version"],
                name="unique_assessment_framework_code_version",
            )
        ]

    def __str__(self) -> str:
        return f"{self.code} v{self.version}"


class AssessmentDimension(TimestampedUUIDModel):
    framework = models.ForeignKey(
        AssessmentFramework,
        on_delete=models.CASCADE,
        related_name="dimensions",
    )
    code = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["framework__code", "display_order", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["framework", "code"],
                name="unique_assessment_dimension_code_per_framework",
            )
        ]

    def __str__(self) -> str:
        return f"{self.framework} / {self.name}"


class AssessmentQuestion(TimestampedUUIDModel):
    class AnswerType(models.TextChoices):
        BOOLEAN = "boolean", "Boolean"
        CHOICE = "choice", "Choice"
        NUMBER = "number", "Number"
        TEXT = "text", "Text"
        JSON = "json", "JSON"

    framework = models.ForeignKey(
        AssessmentFramework,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    dimension = models.ForeignKey(
        AssessmentDimension,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    code = models.CharField(max_length=100)
    text = models.TextField()
    answer_type = models.CharField(max_length=50, choices=AnswerType.choices)
    weight = models.DecimalField(max_digits=8, decimal_places=2, default=1)
    is_required = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["framework__code", "dimension__display_order", "display_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["framework", "code"],
                name="unique_assessment_question_code_per_framework",
            )
        ]

    def __str__(self) -> str:
        return f"{self.code} - {self.text[:80]}"


class Assessment(TimestampedUUIDModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        IN_PROGRESS = "in_progress", "In progress"
        SUBMITTED = "submitted", "Submitted"
        ARCHIVED = "archived", "Archived"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="assessments",
    )
    framework = models.ForeignKey(
        AssessmentFramework,
        on_delete=models.PROTECT,
        related_name="assessments",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_assessments",
    )
    title = models.CharField(max_length=255)
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    started_at = models.DateTimeField(blank=True, null=True)
    submitted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["organization__name", "-created_at"]

    def __str__(self) -> str:
        return self.title


class AssessmentAnswer(TimestampedUUIDModel):
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    question = models.ForeignKey(
        AssessmentQuestion,
        on_delete=models.PROTECT,
        related_name="answers",
    )
    answered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assessment_answers",
        blank=True,
        null=True,
    )
    value = models.JSONField(blank=True, null=True)
    score = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["assessment__title", "question__display_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["assessment", "question"],
                name="unique_assessment_answer_question",
            )
        ]

    def __str__(self) -> str:
        return f"{self.assessment} / {self.question.code}"

