import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

application = get_asgi_application()


def _register_telegram_webhook() -> None:
    try:
        from api.telegram_webhook import ensure_telegram_webhook

        ensure_telegram_webhook()
    except Exception:
        import logging

        logging.getLogger(__name__).exception("Telegram webhook setup failed")


_register_telegram_webhook()
