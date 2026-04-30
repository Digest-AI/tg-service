import logging

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove
from asgiref.sync import sync_to_async
from django.db import transaction
from django.utils import timezone

from api.models import User, VerificationCode
from keyboards.inline import kb_linked, kb_unlinked

logger = logging.getLogger(__name__)

router = Router()

_LINKED_TEXT = (
    "✅ Аккаунт привязан\n\n"
    "Вы получаете уведомления в этом чате.\n"
    "Управляйте настройками на сайте."
)

_NEW_CODE_TEXT = (
    "🔄 Новый код сгенерирован:\n\n"
    "🔑 <code>{code}</code>\n\n"
    "Введите его на сайте в разделе Настройки → Telegram.\n"
    "Код действует 10 минут."
)


def _unlinked_text(code: str) -> str:
    return (
        "👋 Добро пожаловать в Digest.ai!\n\n"
        "Чтобы получать уведомления, привяжите Telegram-аккаунт к профилю на сайте.\n\n"
        "Ваш код привязки:\n\n"
        f"🔑 <code>{code}</code>\n\n"
        "Введите его на сайте в разделе Настройки → Telegram.\n"
        "Код действует 10 минут."
    )


@sync_to_async
def _generate_code(username: str, telegram_id: str) -> VerificationCode:
    with transaction.atomic():
        VerificationCode.objects.filter(username=username).delete()
        return VerificationCode.objects.create(username=username, telegram_id=telegram_id)


async def _send_start(username: str, telegram_id: str, message: Message) -> None:
    if await User.objects.filter(username=username).aexists():
        await message.answer(_LINKED_TEXT, reply_markup=kb_linked())
        return

    try:
        code = await _generate_code(username, telegram_id)
    except Exception as e:
        logger.exception("Failed to generate verification code: %s", e)
        await message.answer("Ошибка при генерации кода. Попробуйте позже.", reply_markup=ReplyKeyboardRemove())
        return

    await message.answer(_unlinked_text(code.code), parse_mode="HTML", reply_markup=kb_unlinked())


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    if message.from_user is None or not message.from_user.username:
        await message.answer("У вашего аккаунта нет username. Установите его в настройках Telegram.")
        return
    await _send_start(message.from_user.username, str(message.from_user.id), message)


@router.callback_query(F.data == "start_link")
async def cb_start_link(callback_query: CallbackQuery) -> None:
    if (
        callback_query.from_user is None
        or not callback_query.from_user.username
        or not isinstance(callback_query.message, Message)
    ):
        return
    await callback_query.answer()
    await _send_start(
        callback_query.from_user.username,
        str(callback_query.from_user.id),
        callback_query.message,
    )


@router.callback_query(F.data == "new_code")
async def cb_new_code(callback_query: CallbackQuery) -> None:
    if (
        callback_query.from_user is None
        or not callback_query.from_user.username
        or not isinstance(callback_query.message, Message)
    ):
        return

    try:
        code = await _generate_code(callback_query.from_user.username, str(callback_query.from_user.id))
    except Exception as e:
        logger.exception("Failed to generate verification code: %s", e)
        await callback_query.answer("Ошибка при генерации кода. Попробуйте позже.", show_alert=True)
        return

    await callback_query.answer()
    await callback_query.message.edit_text(
        _NEW_CODE_TEXT.format(code=code.code),
        parse_mode="HTML",
    )
