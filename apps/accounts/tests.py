from django.contrib.auth import get_user_model
from django.test import TestCase


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

