from rest_framework import serializers

from .models import UserPreference, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field="uuid", read_only=True)

    class Meta:
        model = UserProfile
        fields = (
            "uuid",
            "user",
            "display_name",
            "job_title",
            "phone",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("uuid", "user", "created_at", "updated_at")


class UserPreferenceSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(slug_field="uuid", read_only=True)

    class Meta:
        model = UserPreference
        fields = (
            "uuid",
            "user",
            "locale",
            "timezone",
            "theme",
            "email_notifications_enabled",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("uuid", "user", "created_at", "updated_at")
