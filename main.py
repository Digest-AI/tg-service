import asyncio
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from aiogram import Bot
from django.conf import settings


async def main() -> None:
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    webhook_url = f"{settings.WEBHOOK_HOST}/api/webhook/"
    await bot.set_webhook(webhook_url)
    print(f"Webhook set: {webhook_url}")
    await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
