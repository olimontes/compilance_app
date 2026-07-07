from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Audit fields", {"fields": ("uuid", "created_at", "updated_at")}),
    )
    readonly_fields = ("uuid", "created_at", "updated_at")

