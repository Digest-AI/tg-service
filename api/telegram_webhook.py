import asyncio
import logging

from aiogram import Bot
from django.conf import settings

logger = logging.getLogger(__name__)


async def _set_webhook_async() -> None:
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN is not set; skipping Telegram webhook setup")
        return

    base = (settings.SELF_URL or "").strip().rstrip("/")
    if not base:
        logger.warning("SELF_URL is empty (check HOST); skipping Telegram webhook setup")
        return

    webhook_url = f"{base}/api/webhook/"
    bot = Bot(token=token)
    try:
        await bot.set_webhook(webhook_url)
        logger.info("Telegram webhook registered: %s", webhook_url)
    finally:
        await bot.session.close()


def ensure_telegram_webhook() -> None:
    """Register Telegram webhook URL derived from settings.SELF_URL."""
    asyncio.run(_set_webhook_async())
