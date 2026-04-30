from django.db import models


class User(models.Model):
    public_id = models.CharField(max_length=255, unique=True)
    username = models.CharField(max_length=255, unique=True)
    telegram_id = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ["id"]
