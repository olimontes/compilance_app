from django.db import models

from apps.ai_assets.models import AiUseCase, RiskLevel
from apps.common.models import TimestampedUUIDModel
from apps.organizations.models import Membership, Organization


class Control(TimestampedUUIDModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        DRAFT = "draft", "Draft"
        RETIRED = "retired", "Retired"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="controls",
    )
    code = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    domain = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    class Meta:
        ordering = ["organization__name", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code"],
                name="unique_control_code_per_organization",
            )
        ]

    def __str__(self) -> str:
        return f"{self.code} - {self.title}"


class Risk(TimestampedUUIDModel):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        MITIGATING = "mitigating", "Mitigating"
        ACCEPTED = "accepted", "Accepted"
        CLOSED = "closed", "Closed"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="risks",
    )
    ai_use_case = models.ForeignKey(
        AiUseCase,
        on_delete=models.SET_NULL,
        related_name="risks",
        blank=True,
        null=True,
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    likelihood = models.PositiveSmallIntegerField()
    impact = models.PositiveSmallIntegerField()
    severity = models.CharField(max_length=30, choices=RiskLevel.choices)
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.OPEN,
    )
    controls = models.ManyToManyField(
        Control,
        through="RiskControl",
        related_name="risks",
        blank=True,
    )

    class Meta:
        ordering = ["organization__name", "-created_at"]

    def __str__(self) -> str:
        return self.title


class RiskControl(models.Model):
    risk = models.ForeignKey(
        Risk,
        on_delete=models.CASCADE,
        related_name="risk_controls",
    )
    control = models.ForeignKey(
        Control,
        on_delete=models.CASCADE,
        related_name="risk_controls",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["risk__title", "control__code"]
        constraints = [
            models.UniqueConstraint(
                fields=["risk", "control"],
                name="unique_risk_control",
            )
        ]

    def __str__(self) -> str:
        return f"{self.risk} / {self.control}"


class RiskAssessment(TimestampedUUIDModel):
    risk = models.ForeignKey(
        Risk,
        on_delete=models.CASCADE,
        related_name="assessments",
    )
    assessed_by = models.ForeignKey(
        Membership,
        on_delete=models.SET_NULL,
        related_name="risk_assessments",
        blank=True,
        null=True,
    )
    likelihood = models.PositiveSmallIntegerField()
    impact = models.PositiveSmallIntegerField()
    severity = models.CharField(max_length=30, choices=RiskLevel.choices)
    rationale = models.TextField(blank=True)
    assessed_at = models.DateTimeField()

    class Meta:
        ordering = ["risk__title", "-assessed_at"]

    def __str__(self) -> str:
        return f"{self.risk} assessed at {self.assessed_at:%Y-%m-%d}"


class Policy(TimestampedUUIDModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        UNDER_REVIEW = "under_review", "Under review"
        RETIRED = "retired", "Retired"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="policies",
    )
    code = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    owner_membership = models.ForeignKey(
        Membership,
        on_delete=models.SET_NULL,
        related_name="owned_policies",
        blank=True,
        null=True,
    )
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.DRAFT)
    effective_date = models.DateField(blank=True, null=True)
    review_date = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ["organization__name", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code"],
                name="unique_policy_code_per_organization",
            )
        ]

    def __str__(self) -> str:
        return f"{self.code} - {self.title}"


class ActionPlan(TimestampedUUIDModel):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="action_plans",
    )
    risk = models.ForeignKey(
        Risk,
        on_delete=models.SET_NULL,
        related_name="action_plans",
        blank=True,
        null=True,
    )
    control = models.ForeignKey(
        Control,
        on_delete=models.SET_NULL,
        related_name="action_plans",
        blank=True,
        null=True,
    )
    policy = models.ForeignKey(
        Policy,
        on_delete=models.SET_NULL,
        related_name="action_plans",
        blank=True,
        null=True,
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.OPEN)
    due_date = models.DateField(blank=True, null=True)
    owner_membership = models.ForeignKey(
        Membership,
        on_delete=models.SET_NULL,
        related_name="owned_action_plans",
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["organization__name", "status", "due_date", "title"]

    def __str__(self) -> str:
        return self.title


class ActionItem(TimestampedUUIDModel):
    class Status(models.TextChoices):
        TODO = "todo", "To do"
        IN_PROGRESS = "in_progress", "In progress"
        DONE = "done", "Done"
        BLOCKED = "blocked", "Blocked"
        CANCELLED = "cancelled", "Cancelled"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="action_items",
    )
    action_plan = models.ForeignKey(
        ActionPlan,
        on_delete=models.CASCADE,
        related_name="items",
    )
    risk = models.ForeignKey(
        Risk,
        on_delete=models.SET_NULL,
        related_name="action_items",
        blank=True,
        null=True,
    )
    control = models.ForeignKey(
        Control,
        on_delete=models.SET_NULL,
        related_name="action_items",
        blank=True,
        null=True,
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.TODO)
    due_date = models.DateField(blank=True, null=True)
    owner_membership = models.ForeignKey(
        Membership,
        on_delete=models.SET_NULL,
        related_name="owned_action_items",
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ["organization__name", "status", "due_date", "title"]

    def __str__(self) -> str:
        return self.title
