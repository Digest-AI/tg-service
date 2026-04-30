import secrets
from datetime import timedelta

from django.db import models
from django.utils import timezone

_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
_CODE_LENGTH = 6
_CODE_TTL_MINUTES = 10


class VerificationCode(models.Model):
    code = models.CharField(max_length=_CODE_LENGTH, unique=True)
    username = models.CharField(max_length=255)
    telegram_id = models.CharField(max_length=255)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ["id"]

    def save(self, *args, **kwargs) -> None:
        if not self.pk:
            self.code = self._generate_unique_code()
            self.expires_at = timezone.now() + timedelta(minutes=_CODE_TTL_MINUTES)
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_unique_code() -> str:
        while True:
            code = "".join(secrets.choice(_ALPHABET) for _ in range(_CODE_LENGTH))
            if not VerificationCode.objects.filter(code=code).exists():
                return code

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at
