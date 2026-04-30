import os

from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"
    verbose_name = "API"

    def ready(self) -> None:
        from django.conf import settings

        # In development Django runs two processes (autoreloader + main).
        # RUN_MAIN=true is set only on the main process — start scheduler there.
        # In production (no autoreloader) DEBUG is False, so we always start.
        if not settings.DEBUG or os.environ.get("RUN_MAIN") == "true":
            from scheduler import start_scheduler
            start_scheduler()
