from django.contrib import admin

from .models import (
    Assessment,
    AssessmentAnswer,
    AssessmentDimension,
    AssessmentFramework,
    AssessmentQuestion,
)


@admin.register(AssessmentFramework)
class AssessmentFrameworkAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "version", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("code", "name", "version")
    readonly_fields = ("uuid", "created_at", "updated_at")


@admin.register(AssessmentDimension)
class AssessmentDimensionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "framework", "display_order")
    list_filter = ("framework",)
    search_fields = ("code", "name", "framework__name")
    readonly_fields = ("uuid", "created_at", "updated_at")


@admin.register(AssessmentQuestion)
class AssessmentQuestionAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "framework",
        "dimension",
        "answer_type",
        "weight",
        "is_required",
        "display_order",
    )
    list_filter = ("framework", "dimension", "answer_type", "is_required")
    search_fields = ("code", "text", "framework__name", "dimension__name")
    readonly_fields = ("uuid", "created_at", "updated_at")


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ("title", "organization", "framework", "status", "created_by")
    list_filter = ("status", "organization", "framework")
    search_fields = ("title", "organization__name", "framework__name")
    readonly_fields = ("uuid", "created_at", "updated_at")


@admin.register(AssessmentAnswer)
class AssessmentAnswerAdmin(admin.ModelAdmin):
    list_display = ("assessment", "question", "score", "answered_by", "updated_at")
    list_filter = ("assessment__organization", "question__framework")
    search_fields = ("assessment__title", "question__code", "notes")
    readonly_fields = ("uuid", "created_at", "updated_at")

