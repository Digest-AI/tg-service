from aiogram import Bot
from aiogram.types import Update
from asgiref.sync import async_to_sync
from django.conf import settings
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from dispatcher import dp


@method_decorator(csrf_exempt, name="dispatch")
class TelegramWebhookView(View):
    def post(self, request) -> HttpResponse:
        update = Update.model_validate_json(request.body)

        async def handle() -> None:
            bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
            try:
                await dp.feed_update(bot, update)
            finally:
                await bot.session.close()

        async_to_sync(handle)()
        return HttpResponse(status=200)
