from django.contrib import admin

from .models import Control, Risk, RiskControl


@admin.register(Control)
class ControlAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "organization", "domain", "status", "created_at")
    list_filter = ("status", "domain", "organization")
    search_fields = ("code", "title", "description", "organization__name")
    readonly_fields = ("uuid", "created_at", "updated_at")


class RiskControlInline(admin.TabularInline):
    model = RiskControl
    extra = 0
    autocomplete_fields = ("control",)


@admin.register(Risk)
class RiskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "organization",
        "ai_use_case",
        "likelihood",
        "impact",
        "severity",
        "status",
    )
    list_filter = ("severity", "status", "organization")
    search_fields = ("title", "description", "organization__name", "ai_use_case__name")
    readonly_fields = ("uuid", "created_at", "updated_at")
    inlines = [RiskControlInline]


@admin.register(RiskControl)
class RiskControlAdmin(admin.ModelAdmin):
    list_display = ("risk", "control", "created_at")
    list_filter = ("risk__organization", "control__domain")
    search_fields = ("risk__title", "control__code", "control__title")

