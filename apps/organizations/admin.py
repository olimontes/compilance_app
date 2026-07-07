from django.contrib import admin

from .models import Membership, Organization, OrganizationUnit


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("name", "slug", "tax_id")
    readonly_fields = ("uuid", "created_at", "updated_at")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(OrganizationUnit)
class OrganizationUnitAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "parent", "created_at")
    list_filter = ("organization",)
    search_fields = ("name", "slug", "organization__name")
    readonly_fields = ("uuid", "created_at", "updated_at")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "organization", "role", "status", "created_at")
    list_filter = ("role", "status", "organization")
    search_fields = ("user__username", "user__email", "organization__name")
    readonly_fields = ("uuid", "created_at", "updated_at")

