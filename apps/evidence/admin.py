from django.contrib import admin

from .models import Evidence, EvidenceLink


class EvidenceLinkInline(admin.TabularInline):
    model = EvidenceLink
    extra = 0
    autocomplete_fields = ("risk", "control", "assessment_answer")


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "organization",
        "evidence_type",
        "storage_backend",
        "status",
        "uploaded_by",
        "created_at",
    )
    list_filter = ("evidence_type", "storage_backend", "status", "organization")
    search_fields = ("title", "description", "external_url", "organization__name")
    readonly_fields = ("uuid", "created_at", "updated_at")
    inlines = [EvidenceLinkInline]


@admin.register(EvidenceLink)
class EvidenceLinkAdmin(admin.ModelAdmin):
    list_display = ("evidence", "risk", "control", "assessment_answer", "created_at")
    list_filter = ("evidence__organization",)
    search_fields = (
        "evidence__title",
        "risk__title",
        "control__code",
        "assessment_answer__assessment__title",
    )

