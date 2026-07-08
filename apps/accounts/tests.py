from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from .models import UserPreference, UserProfile


class UserTests(TestCase):
    def test_create_custom_user(self):
        user = get_user_model().objects.create_user(
            username="alice",
            email="alice@example.com",
            password="password-123",
        )

        self.assertEqual(user.username, "alice")
        self.assertEqual(user.email, "alice@example.com")
        self.assertTrue(user.uuid)


class AccountApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="alice",
            email="alice@example.com",
            password="password-123",
            first_name="Alice",
            last_name="Example",
        )
        self.client.force_authenticate(self.user)

    def test_get_current_user_profile_creates_default_profile(self):
        response = self.client.get("/api/user-profile/me/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["display_name"], "Alice Example")
        self.assertEqual(UserProfile.objects.get(user=self.user).display_name, "Alice Example")

    def test_update_current_user_profile(self):
        response = self.client.patch(
            "/api/user-profile/me/",
            {"display_name": "Alice Compliance", "job_title": "Data Engineer"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.display_name, "Alice Compliance")
        self.assertEqual(profile.job_title, "Data Engineer")

    def test_get_current_user_preferences_creates_defaults(self):
        response = self.client.get("/api/user-preferences/me/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["locale"], "pt-BR")
        self.assertEqual(response.data["timezone"], "America/Sao_Paulo")
        self.assertTrue(UserPreference.objects.filter(user=self.user).exists())

    def test_update_current_user_preferences(self):
        response = self.client.patch(
            "/api/user-preferences/me/",
            {"theme": UserPreference.Theme.DARK, "email_notifications_enabled": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        preferences = UserPreference.objects.get(user=self.user)
        self.assertEqual(preferences.theme, UserPreference.Theme.DARK)
        self.assertFalse(preferences.email_notifications_enabled)
