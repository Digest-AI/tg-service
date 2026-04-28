from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

SITE_URL = "https://digest.ai"


def kb_unlinked() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Открыть сайт →", url=f"{SITE_URL}/settings/telegram")],
        [InlineKeyboardButton(text="🔄 Получить новый код", callback_data="new_code")],
    ])


def kb_linked() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Настройки на сайте →", url=f"{SITE_URL}/settings")],
        [InlineKeyboardButton(text="💎 Купить Premium", callback_data="show_premium")],
    ])


def kb_premium() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 месяц · 199 ⭐", callback_data="buy:1m")],
        [InlineKeyboardButton(text="3 месяца · 499 ⭐", callback_data="buy:3m")],
        [InlineKeyboardButton(text="12 месяцев · 1490 ⭐", callback_data="buy:12m")],
    ])


def kb_after_payment() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Перейти на сайт →", url=SITE_URL)],
    ])


def kb_help() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Настройки →", url=f"{SITE_URL}/settings")],
        [InlineKeyboardButton(text="Написать в поддержку", url="https://t.me/digestai_support")],
    ])


def kb_not_linked() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Привязать аккаунт", callback_data="start_link")],
    ])


def kb_recommendation(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подробнее →", url=url)],
    ])


def kb_reminder(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Перейти к событию →", url=url)],
    ])
