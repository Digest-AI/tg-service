from datetime import date, timedelta

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

from keyboards.inline import kb_after_payment, kb_premium

router = Router()

_PREMIUM_TEXT = (
    "💎 Premium подписка\n\n"
    "Снимите ограничения и получайте уведомления без лимитов.\n\n"
    "🆓 Free\n"
    "• До 5 уведомлений в день\n"
    "• Только рекомендации\n\n"
    "💎 Premium\n"
    "• Безлимитные уведомления\n"
    "• Напоминания об избранных событиях\n"
    "• Приоритетная доставка"
)

_PLANS: dict[str, tuple[str, int, int]] = {
    "buy:1m":  ("Premium — 1 месяц",   199,  30),
    "buy:3m":  ("Premium — 3 месяца",  499,  90),
    "buy:12m": ("Premium — 12 месяцев", 1490, 365),
}


@router.message(Command("premium"))
async def cmd_premium(message: Message) -> None:
    await message.answer(_PREMIUM_TEXT, reply_markup=kb_premium())


@router.callback_query(F.data == "show_premium")
async def cb_show_premium(callback_query: CallbackQuery) -> None:
    if not isinstance(callback_query.message, Message):
        return
    await callback_query.answer()
    await callback_query.message.answer(_PREMIUM_TEXT, reply_markup=kb_premium())


@router.callback_query(F.data.startswith("buy:"))
async def cb_buy(callback_query: CallbackQuery) -> None:
    if not isinstance(callback_query.message, Message) or callback_query.data not in _PLANS:
        return

    label, amount, _ = _PLANS[callback_query.data]
    await callback_query.answer()
    await callback_query.message.answer_invoice(
        title="Digest.ai Premium",
        description=label,
        payload=callback_query.data,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=label, amount=amount)],
    )


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery) -> None:
    await query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message) -> None:
    if message.successful_payment is None:
        return

    payload = message.successful_payment.invoice_payload
    label, _, days = _PLANS.get(payload, ("Неизвестный план", 0, 0))
    expires = date.today() + timedelta(days=days)

    await message.answer(
        f"✅ Подписка активирована!\n\n"
        f"План: {label}\n"
        f"Действует до: {expires.strftime('%d.%m.%Y')}\n\n"
        "Теперь вы получаете уведомления без ограничений.",
    )
