"""
Manual webhook registration (optional).

Webhook is set automatically when the WSGI/ASGI application loads.
Use this script if you need to refresh the webhook without restarting the server.
"""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from api.telegram_webhook import ensure_telegram_webhook

if __name__ == "__main__":
    ensure_telegram_webhook()
    print("Done — check logs for the registered webhook URL.")
