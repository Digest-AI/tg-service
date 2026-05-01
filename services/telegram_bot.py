"""
Shared aiogram Bot factory.

On PythonAnywhere free tier, outbound HTTPS to api.telegram.org must use their HTTP proxy
(https://help.pythonanywhere.com/pages/403ForbiddenError/). Set TELEGRAM_HTTP_PROXY or rely on
auto-detection via PYTHONANYWHERE_DOMAIN in Django settings.
"""

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from django.conf import settings


def make_bot(token: str | None = None) -> Bot:
    """Build a Bot; uses TELEGRAM_HTTP_PROXY from settings when set."""
    tok = (token or getattr(settings, "TELEGRAM_BOT_TOKEN", None) or "").strip()
    if not tok:
        raise ValueError("Telegram bot token is missing")

    proxy = getattr(settings, "TELEGRAM_HTTP_PROXY", None)
    if proxy:
        session = AiohttpSession(proxy=proxy)
        return Bot(token=tok, session=session)
    return Bot(token=tok)
