from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.common.models import TimestampedUUIDModel


class User(TimestampedUUIDModel, AbstractUser):
    email = models.EmailField(unique=True)

    class Meta:
        ordering = ["username"]

    def __str__(self) -> str:
        return self.get_username()


class UserProfile(TimestampedUUIDModel):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    display_name = models.CharField(max_length=255)
    job_title = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ["user__username"]

    def __str__(self) -> str:
        return self.display_name or self.user.get_username()


class UserPreference(TimestampedUUIDModel):
    class Theme(models.TextChoices):
        SYSTEM = "system", "System"
        LIGHT = "light", "Light"
        DARK = "dark", "Dark"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="preferences",
    )
    locale = models.CharField(max_length=20, default="pt-BR")
    timezone = models.CharField(max_length=100, default="America/Sao_Paulo")
    theme = models.CharField(max_length=20, choices=Theme.choices, default=Theme.SYSTEM)
    email_notifications_enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ["user__username"]

    def __str__(self) -> str:
        return f"{self.user} preferences"
