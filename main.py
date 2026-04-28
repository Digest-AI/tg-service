import asyncio
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from aiogram import Bot, Dispatcher
from django.conf import settings

from handlers import help, start, subscription
from middlewares.check_linked import CheckLinkedMiddleware


async def main() -> None:
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()

    dp.message.outer_middleware(CheckLinkedMiddleware())

    dp.include_router(start.router)
    dp.include_router(subscription.router)
    dp.include_router(help.router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
