from asgiref.sync import async_to_sync
from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from django.conf import settings
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from api.models import User
from api.serializers import RecommendationSerializer
from utils.exceptions.classes import NotFound


class RecommendationView(APIView):
    def post(self, request: Request) -> Response:
        serializer = RecommendationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        try:
            user = User.objects.get(username=data["username"])
        except User.DoesNotExist:
            raise NotFound(detail="user_not_found", attr="username")

        text = (
            "💡 Вам может быть интересно\n\n"
            f"<b>{data['title']}</b>\n"
            f"📅 {data['date']}\n\n"
            f"{data['description']}"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Подробнее →", url=data["url"])],
        ])

        async def send() -> None:
            bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
            await bot.send_message(user.telegram_id, text, parse_mode="HTML", reply_markup=keyboard)
            await bot.session.close()

        async_to_sync(send)()

        return Response(status=status.HTTP_204_NO_CONTENT)
