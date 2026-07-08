from django.contrib import admin

from .models import AuditEvent, DataChangeLog


class DataChangeLogInline(admin.TabularInline):
    model = DataChangeLog
    extra = 0
    readonly_fields = ("uuid", "created_at")


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = (
        "event_type",
        "organization",
        "actor_user",
        "entity_type",
        "entity_uuid",
        "created_at",
    )
    list_filter = ("event_type", "entity_type", "organization")
    search_fields = ("event_type", "entity_type", "actor_user__username")
    readonly_fields = ("uuid", "created_at")
    inlines = [DataChangeLogInline]


@admin.register(DataChangeLog)
class DataChangeLogAdmin(admin.ModelAdmin):
    list_display = ("audit_event", "entity_type", "entity_uuid", "action", "created_at")
    list_filter = ("action", "entity_type")
    search_fields = ("entity_type", "entity_uuid", "audit_event__event_type")
    readonly_fields = ("uuid", "created_at")
