from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from api.models import User
from keyboards.inline import kb_not_linked

_NOT_LINKED_TEXT = (
    "⚠️ Аккаунт не привязан\n\n"
    "Запустите /start чтобы получить код привязки и соединить "
    "Telegram с вашим профилем на сайте."
)

_ALLOWED_COMMANDS = ("/start", "/help", "/premium")


class CheckLinkedMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message) or event.from_user is None:
            return await handler(event, data)

        text = event.text or ""
        if any(text.startswith(cmd) for cmd in _ALLOWED_COMMANDS):
            return await handler(event, data)

        username = event.from_user.username
        if not username or not await User.objects.filter(username=username).aexists():
            await event.answer(_NOT_LINKED_TEXT, reply_markup=kb_not_linked())
            return None

        return await handler(event, data)
