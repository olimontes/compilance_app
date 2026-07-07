from django.contrib import admin

from .models import AiTool, AiUseCase, AiVendor


@admin.register(AiVendor)
class AiVendorAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "risk_level", "created_at")
    list_filter = ("risk_level", "organization")
    search_fields = ("name", "website", "organization__name")
    readonly_fields = ("uuid", "created_at", "updated_at")


@admin.register(AiTool)
class AiToolAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "organization",
        "vendor",
        "category",
        "status",
        "handles_personal_data",
        "handles_sensitive_data",
    )
    list_filter = (
        "status",
        "category",
        "handles_personal_data",
        "handles_sensitive_data",
        "organization",
    )
    search_fields = ("name", "vendor__name", "organization__name")
    readonly_fields = ("uuid", "created_at", "updated_at")


@admin.register(AiUseCase)
class AiUseCaseAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "organization",
        "ai_tool",
        "organization_unit",
        "risk_level",
        "lifecycle_stage",
    )
    list_filter = (
        "risk_level",
        "lifecycle_stage",
        "data_classification",
        "organization",
    )
    search_fields = ("name", "business_area", "organization__name", "ai_tool__name")
    readonly_fields = ("uuid", "created_at", "updated_at")

