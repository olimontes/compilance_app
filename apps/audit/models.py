import uuid

from django.conf import settings
from django.db import models

from apps.common.models import TimestampedUUIDModel
from apps.organizations.models import Organization


class AuditEvent(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        related_name="audit_events",
        blank=True,
        null=True,
    )
    actor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="audit_events",
        blank=True,
        null=True,
    )
    event_type = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=100)
    entity_uuid = models.UUIDField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "created_at"]),
            models.Index(fields=["event_type"]),
            models.Index(fields=["entity_type", "entity_uuid"]),
        ]

    def __str__(self) -> str:
        return self.event_type


class DataChangeLog(TimestampedUUIDModel):
    class Action(models.TextChoices):
        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"

    audit_event = models.ForeignKey(
        AuditEvent,
        on_delete=models.CASCADE,
        related_name="change_logs",
    )
    entity_type = models.CharField(max_length=100)
    entity_uuid = models.UUIDField(blank=True, null=True)
    action = models.CharField(max_length=30, choices=Action.choices)
    before = models.JSONField(blank=True, null=True)
    after = models.JSONField(blank=True, null=True)
    changed_fields = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["entity_type", "entity_uuid"]),
            models.Index(fields=["action"]),
        ]

    def __str__(self) -> str:
        return f"{self.action} {self.entity_type}"
