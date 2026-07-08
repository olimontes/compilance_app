from django.db import models

from apps.common.models import TimestampedUUIDModel
from apps.organizations.models import Membership, Organization, OrganizationUnit


class RiskLevel(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    CRITICAL = "critical", "Critical"


class AiVendor(TimestampedUUIDModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="ai_vendors",
    )
    name = models.CharField(max_length=255)
    website = models.URLField(max_length=500, blank=True)
    risk_level = models.CharField(
        max_length=30,
        choices=RiskLevel.choices,
        default=RiskLevel.MEDIUM,
    )

    class Meta:
        ordering = ["organization__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"],
                name="unique_ai_vendor_name_per_organization",
            )
        ]

    def __str__(self) -> str:
        return self.name


class AiTool(TimestampedUUIDModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        UNDER_REVIEW = "under_review", "Under review"
        SUSPENDED = "suspended", "Suspended"
        RETIRED = "retired", "Retired"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="ai_tools",
    )
    vendor = models.ForeignKey(
        AiVendor,
        on_delete=models.SET_NULL,
        related_name="ai_tools",
        blank=True,
        null=True,
    )
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    handles_personal_data = models.BooleanField(default=False)
    handles_sensitive_data = models.BooleanField(default=False)

    class Meta:
        ordering = ["organization__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"],
                name="unique_ai_tool_name_per_organization",
            )
        ]

    def __str__(self) -> str:
        return self.name


class AiModel(TimestampedUUIDModel):
    class ModelType(models.TextChoices):
        TEXT = "text", "Text"
        IMAGE = "image", "Image"
        AUDIO = "audio", "Audio"
        MULTIMODAL = "multimodal", "Multimodal"
        EMBEDDING = "embedding", "Embedding"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        UNDER_REVIEW = "under_review", "Under review"
        DEPRECATED = "deprecated", "Deprecated"
        RETIRED = "retired", "Retired"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="ai_models",
    )
    ai_tool = models.ForeignKey(
        AiTool,
        on_delete=models.SET_NULL,
        related_name="ai_models",
        blank=True,
        null=True,
    )
    name = models.CharField(max_length=255)
    provider_model_id = models.CharField(max_length=255, blank=True)
    model_type = models.CharField(max_length=30, choices=ModelType.choices, default=ModelType.TEXT)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.ACTIVE)
    risk_level = models.CharField(max_length=30, choices=RiskLevel.choices, default=RiskLevel.MEDIUM)

    class Meta:
        ordering = ["organization__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"],
                name="unique_ai_model_name_per_organization",
            )
        ]

    def __str__(self) -> str:
        return self.name


class AiUseCase(TimestampedUUIDModel):
    class DataClassification(models.TextChoices):
        PUBLIC = "public", "Public"
        INTERNAL = "internal", "Internal"
        CONFIDENTIAL = "confidential", "Confidential"
        RESTRICTED = "restricted", "Restricted"

    class LifecycleStage(models.TextChoices):
        IDEA = "idea", "Idea"
        PILOT = "pilot", "Pilot"
        PRODUCTION = "production", "Production"
        SUSPENDED = "suspended", "Suspended"
        RETIRED = "retired", "Retired"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="ai_use_cases",
    )
    ai_tool = models.ForeignKey(
        AiTool,
        on_delete=models.SET_NULL,
        related_name="ai_use_cases",
        blank=True,
        null=True,
    )
    organization_unit = models.ForeignKey(
        OrganizationUnit,
        on_delete=models.SET_NULL,
        related_name="ai_use_cases",
        blank=True,
        null=True,
    )
    name = models.CharField(max_length=255)
    business_area = models.CharField(max_length=150, blank=True)
    purpose = models.TextField()
    data_classification = models.CharField(
        max_length=50,
        choices=DataClassification.choices,
        default=DataClassification.INTERNAL,
    )
    risk_level = models.CharField(
        max_length=30,
        choices=RiskLevel.choices,
        default=RiskLevel.MEDIUM,
    )
    lifecycle_stage = models.CharField(
        max_length=30,
        choices=LifecycleStage.choices,
        default=LifecycleStage.IDEA,
    )

    class Meta:
        ordering = ["organization__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"],
                name="unique_ai_use_case_name_per_organization",
            )
        ]

    def __str__(self) -> str:
        return self.name


class DataSource(TimestampedUUIDModel):
    class SourceType(models.TextChoices):
        DATABASE = "database", "Database"
        DOCUMENT = "document", "Document"
        API = "api", "API"
        USER_INPUT = "user_input", "User input"
        LOG = "log", "Log"
        OTHER = "other", "Other"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="data_sources",
    )
    ai_use_case = models.ForeignKey(
        AiUseCase,
        on_delete=models.SET_NULL,
        related_name="data_sources",
        blank=True,
        null=True,
    )
    name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=30, choices=SourceType.choices, default=SourceType.OTHER)
    description = models.TextField(blank=True)
    data_classification = models.CharField(
        max_length=50,
        choices=AiUseCase.DataClassification.choices,
        default=AiUseCase.DataClassification.INTERNAL,
    )
    contains_personal_data = models.BooleanField(default=False)
    contains_sensitive_data = models.BooleanField(default=False)

    class Meta:
        ordering = ["organization__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "name"],
                name="unique_data_source_name_per_organization",
            )
        ]

    def __str__(self) -> str:
        return self.name


class AiAssetOwner(TimestampedUUIDModel):
    class Responsibility(models.TextChoices):
        BUSINESS_OWNER = "business_owner", "Business owner"
        TECHNICAL_OWNER = "technical_owner", "Technical owner"
        PRIVACY_OWNER = "privacy_owner", "Privacy owner"
        SECURITY_OWNER = "security_owner", "Security owner"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="ai_asset_owners",
    )
    ai_use_case = models.ForeignKey(
        AiUseCase,
        on_delete=models.CASCADE,
        related_name="asset_owners",
    )
    membership = models.ForeignKey(
        Membership,
        on_delete=models.CASCADE,
        related_name="ai_asset_ownerships",
    )
    responsibility = models.CharField(
        max_length=50,
        choices=Responsibility.choices,
        default=Responsibility.BUSINESS_OWNER,
    )

    class Meta:
        ordering = ["organization__name", "ai_use_case__name", "responsibility"]
        constraints = [
            models.UniqueConstraint(
                fields=["ai_use_case", "membership", "responsibility"],
                name="unique_ai_asset_owner_responsibility",
            )
        ]

    def __str__(self) -> str:
        return f"{self.membership} owns {self.ai_use_case}"
