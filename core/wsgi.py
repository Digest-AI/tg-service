import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

application = get_wsgi_application()


def _register_telegram_webhook() -> None:
    """Runs when the WSGI worker loads (not during migrate/shell)."""
    try:
        from api.telegram_webhook import ensure_telegram_webhook

        ensure_telegram_webhook()
    except Exception:
        import logging

        logging.getLogger(__name__).exception("Telegram webhook setup failed")


_register_telegram_webhook()
