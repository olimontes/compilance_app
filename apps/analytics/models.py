from django.db import models

from apps.common.models import TimestampedUUIDModel
from apps.organizations.models import Organization


class MetricDefinition(TimestampedUUIDModel):
    class ValueType(models.TextChoices):
        INTEGER = "integer", "Integer"
        DECIMAL = "decimal", "Decimal"
        PERCENTAGE = "percentage", "Percentage"
        CURRENCY = "currency", "Currency"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        DRAFT = "draft", "Draft"
        RETIRED = "retired", "Retired"

    key = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    value_type = models.CharField(max_length=30, choices=ValueType.choices)
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    class Meta:
        ordering = ["key"]

    def __str__(self) -> str:
        return self.key


class MetricSnapshot(TimestampedUUIDModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="metric_snapshots",
    )
    metric_definition = models.ForeignKey(
        MetricDefinition,
        on_delete=models.PROTECT,
        related_name="snapshots",
    )
    metric_value = models.DecimalField(max_digits=18, decimal_places=4)
    dimensions = models.JSONField(default=dict, blank=True)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    computed_at = models.DateTimeField()

    class Meta:
        ordering = ["organization__name", "metric_definition__key", "-computed_at"]
        indexes = [
            models.Index(fields=["organization", "computed_at"]),
            models.Index(fields=["metric_definition", "period_start", "period_end"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "organization",
                    "metric_definition",
                    "period_start",
                    "period_end",
                ],
                name="unique_metric_snapshot_period",
            )
        ]

    def __str__(self) -> str:
        return f"{self.metric_definition} / {self.organization}"


class DataQualityCheck(TimestampedUUIDModel):
    class Status(models.TextChoices):
        PASSED = "passed", "Passed"
        FAILED = "failed", "Failed"
        WARNING = "warning", "Warning"
        ERROR = "error", "Error"

    check_key = models.CharField(max_length=100)
    target_table = models.CharField(max_length=100)
    status = models.CharField(max_length=30, choices=Status.choices)
    result = models.JSONField(default=dict, blank=True)
    executed_at = models.DateTimeField()

    class Meta:
        ordering = ["-executed_at", "check_key"]
        indexes = [
            models.Index(fields=["check_key", "executed_at"]),
            models.Index(fields=["target_table", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.check_key} / {self.status}"


class IngestionRun(TimestampedUUIDModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    source_name = models.CharField(max_length=150)
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING,
    )
    started_at = models.DateTimeField()
    finished_at = models.DateTimeField(blank=True, null=True)
    rows_read = models.PositiveIntegerField(default=0)
    rows_written = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at", "source_name"]
        indexes = [
            models.Index(fields=["source_name", "started_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.source_name} / {self.status}"

