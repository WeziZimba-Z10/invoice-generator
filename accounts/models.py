from django.conf import settings
from django.db import models

from config.currencies import CURRENCY_CHOICES, DEFAULT_CURRENCY


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    default_currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default=DEFAULT_CURRENCY,
    )

    def __str__(self):
        return f"Profile for {self.user}"


def get_profile(user):
    profile, _created = Profile.objects.get_or_create(user=user)
    return profile