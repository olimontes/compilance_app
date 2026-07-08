from rest_framework import serializers

from .models import AuditEvent, DataChangeLog


class AuditEventSerializer(serializers.ModelSerializer):
    organization = serializers.SlugRelatedField(slug_field="uuid", read_only=True)
    actor_user = serializers.SlugRelatedField(slug_field="uuid", read_only=True)

    class Meta:
        model = AuditEvent
        fields = (
            "uuid",
            "organization",
            "actor_user",
            "event_type",
            "entity_type",
            "entity_uuid",
            "ip_address",
            "user_agent",
            "metadata",
            "created_at",
        )
        read_only_fields = fields


class DataChangeLogSerializer(serializers.ModelSerializer):
    audit_event = serializers.SlugRelatedField(slug_field="uuid", read_only=True)

    class Meta:
        model = DataChangeLog
        fields = (
            "uuid",
            "audit_event",
            "entity_type",
            "entity_uuid",
            "action",
            "before",
            "after",
            "changed_fields",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields
