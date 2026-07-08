from django.contrib import admin

from .models import ActionItem, ActionPlan, Control, Policy, Risk, RiskAssessment, RiskControl


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


@admin.register(RiskAssessment)
class RiskAssessmentAdmin(admin.ModelAdmin):
    list_display = ("risk", "severity", "likelihood", "impact", "assessed_by", "assessed_at")
    list_filter = ("severity", "risk__organization")
    search_fields = ("risk__title", "rationale", "assessed_by__user__username")
    readonly_fields = ("uuid", "created_at", "updated_at")


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "organization", "status", "owner_membership", "review_date")
    list_filter = ("status", "organization")
    search_fields = ("code", "title", "description", "organization__name")
    readonly_fields = ("uuid", "created_at", "updated_at")


class ActionItemInline(admin.TabularInline):
    model = ActionItem
    extra = 0


@admin.register(ActionPlan)
class ActionPlanAdmin(admin.ModelAdmin):
    list_display = ("title", "organization", "status", "due_date", "owner_membership")
    list_filter = ("status", "organization")
    search_fields = ("title", "description", "organization__name")
    readonly_fields = ("uuid", "created_at", "updated_at")
    inlines = [ActionItemInline]


@admin.register(ActionItem)
class ActionItemAdmin(admin.ModelAdmin):
    list_display = ("title", "organization", "action_plan", "status", "due_date", "owner_membership")
    list_filter = ("status", "organization")
    search_fields = ("title", "description", "action_plan__title", "organization__name")
    readonly_fields = ("uuid", "created_at", "updated_at")
