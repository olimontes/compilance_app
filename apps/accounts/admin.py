from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, UserPreference, UserProfile


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Audit fields", {"fields": ("uuid", "created_at", "updated_at")}),
    )
    readonly_fields = ("uuid", "created_at", "updated_at")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "job_title", "created_at")
    search_fields = ("user__username", "user__email", "display_name", "job_title")
    readonly_fields = ("uuid", "created_at", "updated_at")


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "locale", "timezone", "theme", "email_notifications_enabled")
    list_filter = ("theme", "email_notifications_enabled")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("uuid", "created_at", "updated_at")
