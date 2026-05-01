import asyncio
import logging
from collections import defaultdict
from datetime import datetime

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from django.conf import settings
from django.core.cache import cache

from api.models import User
from services.parser import get_events_by_daterange
from services.recommendations import get_all_new_recommendations
from services.telegram_bot import make_bot

logger = logging.getLogger(__name__)

_LOCK_KEY = "morning_digest_running"
_LOCK_TTL = 3600  # 1 hour hard ceiling — prevents stale lock on crash


def _format_date(date_str: str | None) -> str:
    if not date_str:
        return "Дата уточняется"
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return date_str


def _event_url(event: dict) -> str:
    if event.get("url"):
        return event["url"]
    ticket_links = event.get("ticketLinks") or {}
    if ticket_links:
        return next(iter(ticket_links.values()))
    return ""


def _build_message(event: dict) -> tuple[str, InlineKeyboardMarkup]:
    title = event.get("title") or event.get("titleRu") or "Событие"
    date_str = _format_date(event.get("dateStart") or event.get("date_start"))
    description = (event.get("description") or event.get("descriptionRu") or "")[:300]
    url = _event_url(event)

    text = (
        "💡 Вам может быть интересно\n\n"
        f"<b>{title}</b>\n"
        f"📅 {date_str}\n\n"
        f"{description}"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подробнее →", url=url)],
    ])
    return text, keyboard


async def _send_events(telegram_id: str, events: list[dict]) -> None:
    bot = make_bot()
    try:
        for event in events:
            text, keyboard = _build_message(event)
            await bot.send_message(telegram_id, text, parse_mode="HTML", reply_markup=keyboard)
    finally:
        await bot.session.close()


def morning_digest_job() -> None:
    if not cache.add(_LOCK_KEY, True, _LOCK_TTL):
        logger.warning("Morning digest already running, skipping duplicate execution")
        return

    try:
        _run_digest()
    finally:
        cache.delete(_LOCK_KEY)


def _run_digest() -> None:
    logger.info("Morning digest job started")

    # Step 1: single request — all new recommendations across all users
    all_recs = get_all_new_recommendations()
    if not all_recs:
        logger.info("No new recommendations")
        return

    # Step 2: group events by publicId
    events_by_public_id: dict[str, list[dict]] = defaultdict(list)
    for rec in all_recs:
        public_id = rec.get("publicId") or rec.get("public_id") or rec.get("userId")
        event = rec.get("event")
        if public_id and event:
            events_by_public_id[public_id].append(event)

    if not events_by_public_id:
        logger.info("No recommendations with event data")
        return

    # Step 3: compute overall date range from all events
    all_dates = [
        (event.get("dateStart") or event.get("date_start") or "")[:10]
        for events in events_by_public_id.values()
        for event in events
    ]
    all_dates = [d for d in all_dates if d]

    if not all_dates:
        logger.info("No event dates found in recommendations")
        return

    date_from = min(all_dates)
    date_to = max(all_dates)
    logger.info("Fetching parser events for range %s – %s", date_from, date_to)

    # Step 4: get fresh event data from parser for that date range
    parser_events = get_events_by_daterange(date_from, date_to)
    events_by_id = {str(e["id"]): e for e in parser_events}

    # Step 5: send each user their recommended events (enriched with fresh parser data)
    users_qs = User.objects.filter(public_id__in=events_by_public_id.keys())
    users_by_public_id = {u.public_id: u for u in users_qs}

    for public_id, events in events_by_public_id.items():
        user = users_by_public_id.get(public_id)
        if not user:
            logger.warning("No tg user found for public_id=%s", public_id)
            continue

        fresh_events = [
            events_by_id.get(str(event.get("id")), event)
            for event in events
        ]

        try:
            asyncio.run(_send_events(user.telegram_id, fresh_events))
            logger.info("Sent %d events to telegram_id=%s", len(fresh_events), user.telegram_id)
        except Exception:
            logger.exception("Failed to send digest to telegram_id=%s", user.telegram_id)

    logger.info("Morning digest job completed")

