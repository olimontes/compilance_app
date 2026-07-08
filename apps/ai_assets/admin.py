from django.contrib import admin

from .models import AiAssetOwner, AiModel, AiTool, AiUseCase, AiVendor, DataSource


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


@admin.register(AiModel)
class AiModelAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "ai_tool", "model_type", "status", "risk_level")
    list_filter = ("model_type", "status", "risk_level", "organization")
    search_fields = ("name", "provider_model_id", "ai_tool__name", "organization__name")
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


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "organization",
        "ai_use_case",
        "source_type",
        "data_classification",
        "contains_personal_data",
        "contains_sensitive_data",
    )
    list_filter = (
        "source_type",
        "data_classification",
        "contains_personal_data",
        "contains_sensitive_data",
        "organization",
    )
    search_fields = ("name", "description", "ai_use_case__name", "organization__name")
    readonly_fields = ("uuid", "created_at", "updated_at")


@admin.register(AiAssetOwner)
class AiAssetOwnerAdmin(admin.ModelAdmin):
    list_display = ("ai_use_case", "membership", "organization", "responsibility")
    list_filter = ("responsibility", "organization")
    search_fields = ("ai_use_case__name", "membership__user__username", "membership__user__email")
    readonly_fields = ("uuid", "created_at", "updated_at")
