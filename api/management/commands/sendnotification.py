import asyncio

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from django.core.management.base import BaseCommand, CommandParser

from services.telegram_bot import make_bot


class Command(BaseCommand):
    help = "Send a test notification to a Telegram user"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("telegram_id", type=str, help="Telegram user ID")
        parser.add_argument(
            "--type",
            choices=["recommendation", "reminder"],
            default="recommendation",
            dest="notification_type",
        )

    def handle(self, *args, **kwargs) -> None:
        asyncio.run(self._send(kwargs["telegram_id"], kwargs["notification_type"]))

    async def _send(self, telegram_id: str, notification_type: str) -> None:
        bot = make_bot()

        if notification_type == "recommendation":
            text = (
                "💡 Вам может быть интересно\n\n"
                "<b>Конференция по AI в Москве</b>\n"
                "📅 15 мая 2026\n\n"
                "Ведущие эксперты обсудят тренды и кейсы применения AI в бизнесе."
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Подробнее →", url="https://digest.ai/events/1")],
            ])
        else:
            text = (
                "⏰ Напоминание\n\n"
                "Событие из вашего Избранного начнётся через 30 минут:\n\n"
                "<b>Вебинар: Монетизация Telegram-ботов</b>"
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Перейти к событию →", url="https://digest.ai/events/1")],
            ])

        await bot.send_message(telegram_id, text, parse_mode="HTML", reply_markup=keyboard)
        await bot.session.close()
        self.stdout.write(self.style.SUCCESS(f"Notification sent to {telegram_id}"))
