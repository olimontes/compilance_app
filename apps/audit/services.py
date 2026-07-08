from decimal import Decimal

from .models import AuditEvent, DataChangeLog


def log_create_event(*, actor_user, organization, instance, event_type, metadata=None):
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
        after=_safe_snapshot(instance),
        changed_fields=list(_safe_snapshot(instance).keys()),
    )
    return event


def _safe_snapshot(instance):
    snapshot = {}
    for field in instance._meta.fields:
        if field.name in {"password", "metadata", "before", "after"}:
            continue
        value = getattr(instance, field.attname)
        snapshot[field.name] = _serialize_value(value)
    return snapshot


def _serialize_value(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "hex"):
        return str(value)
    if isinstance(value, Decimal):
        return str(value)
    return value
