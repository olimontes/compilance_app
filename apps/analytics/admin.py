from django.contrib import admin

from .models import DataQualityCheck, IngestionRun, MetricDefinition, MetricSnapshot


@admin.register(MetricDefinition)
class MetricDefinitionAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "value_type", "status", "created_at")
    list_filter = ("value_type", "status")
    search_fields = ("key", "name", "description")
    readonly_fields = ("uuid", "created_at", "updated_at")


@admin.register(MetricSnapshot)
class MetricSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "metric_definition",
        "organization",
        "metric_value",
        "period_start",
        "period_end",
        "computed_at",
    )
    list_filter = ("metric_definition", "organization", "computed_at")
    search_fields = ("metric_definition__key", "organization__name")
    readonly_fields = ("uuid", "created_at", "updated_at")


@admin.register(DataQualityCheck)
class DataQualityCheckAdmin(admin.ModelAdmin):
    list_display = ("check_key", "target_table", "status", "executed_at")
    list_filter = ("status", "target_table")
    search_fields = ("check_key", "target_table")
    readonly_fields = ("uuid", "created_at", "updated_at")


@admin.register(IngestionRun)
class IngestionRunAdmin(admin.ModelAdmin):
    list_display = (
        "source_name",
        "status",
        "started_at",
        "finished_at",
        "rows_read",
        "rows_written",
    )
    list_filter = ("status", "source_name")
    search_fields = ("source_name", "error_message")
    readonly_fields = ("uuid", "created_at", "updated_at")
