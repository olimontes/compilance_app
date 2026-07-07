from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.common.models import TimestampedUUIDModel


class User(TimestampedUUIDModel, AbstractUser):
    email = models.EmailField(unique=True)

    class Meta:
        ordering = ["username"]

    def __str__(self) -> str:
        return self.get_username()

