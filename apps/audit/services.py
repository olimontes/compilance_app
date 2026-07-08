from decimal import Decimal

from django.db import models

from .models import AuditEvent, DataChangeLog


SENSITIVE_SNAPSHOT_FIELD_NAMES = {
    "after",
    "before",
    "checksum",
    "description",
    "email",
    "error_message",
    "external_url",
    "file_path",
    "metadata",
    "notes",
    "password",
    "phone",
    "rationale",
    "tax_id",
    "value",
}

SENSITIVE_SNAPSHOT_FIELD_TYPES = (
    models.FileField,
    models.JSONField,
    models.TextField,
    models.URLField,
)


def log_create_event(*, actor_user, organization, instance, event_type, metadata=None):
    snapshot = _safe_snapshot(instance)
    event = AuditEvent.objects.create(
        organization=organization,
        actor_user=actor_user if getattr(actor_user, "is_authenticated", False) else None,
        event_type=event_type,
        entity_type=instance.__class__.__name__,
        entity_uuid=getattr(instance, "uuid", None),
        metadata=metadata or {},
    )
    DataChangeLog.objects.create(
        audit_event=event,
        entity_type=instance.__class__.__name__,
        entity_uuid=getattr(instance, "uuid", None),
        action=DataChangeLog.Action.CREATE,
        before=None,
        after=snapshot,
        changed_fields=list(snapshot.keys()),
    )
    return event


def _safe_snapshot(instance):
    snapshot = {}
    for field in instance._meta.fields:
        if _should_skip_snapshot_field(field):
            continue
        value = getattr(instance, field.attname)
        snapshot[field.name] = _serialize_value(value)
    return snapshot


def _should_skip_snapshot_field(field):
    return field.name in SENSITIVE_SNAPSHOT_FIELD_NAMES or isinstance(field, SENSITIVE_SNAPSHOT_FIELD_TYPES)


def _serialize_value(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "hex"):
        return str(value)
    if isinstance(value, Decimal):
        return str(value)
    return value
