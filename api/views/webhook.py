from aiogram.types import Update
from asgiref.sync import async_to_sync
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from dispatcher import dp
from services.telegram_bot import make_bot


@method_decorator(csrf_exempt, name="dispatch")
class TelegramWebhookView(View):
    def post(self, request) -> HttpResponse:
        try:
            update = Update.model_validate_json(request.body)
        except Exception:
            # Always return 200 to Telegram — non-200 causes infinite retries
            return HttpResponse(status=200)

        async def handle() -> None:
            bot = make_bot()
            try:
                await dp.feed_update(bot, update)
            finally:
                await bot.session.close()

        async_to_sync(handle)()
        return HttpResponse(status=200)
