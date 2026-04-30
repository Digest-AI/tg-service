from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from keyboards.inline import kb_help

router = Router()

_HELP_TEXT = (
    "ℹ️ Помощь\n\n"
    "Этот бот отправляет уведомления от Digest.ai:\n\n"
    "• 💡 Рекомендации событий по вашим интересам\n"
    "• ⏰ Напоминания о событиях из Избранного\n\n"
    "Настройки уведомлений — на сайте в разделе Профиль → Telegram.\n\n"
    "Проблема с привязкой? Напишите нам:\n"
    "support@digest.ai"
)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(_HELP_TEXT, reply_markup=kb_help())
