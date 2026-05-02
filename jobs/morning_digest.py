import asyncio
import logging
from collections import defaultdict
from datetime import datetime

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from django.core.cache import cache

from api.models import User
from services.parser import get_events_by_ids
from services.recommendations import get_all_new_recommendations
from services.telegram_bot import make_bot

logger = logging.getLogger(__name__)

_LOCK_KEY = "morning_digest_running"
_LOCK_TTL = 3600  # 1 hour hard ceiling — prevents stale lock on crash


def _rec_user_id(rec: dict) -> str | None:
    raw = (
        rec.get("user_id")
        or rec.get("userId")
        or rec.get("public_id")
        or rec.get("publicId")
    )
    if raw is None:
        return None
    s = str(raw).strip()
    return s or None


def _rec_event_id(rec: dict) -> int | None:
    raw = rec.get("event_id")
    if raw is None:
        raw = rec.get("eventId")
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _format_date(date_str: str | None) -> str:
    if not date_str:
        return "Дата уточняется"
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return date_str


def _event_url(event: dict) -> str:
    url = event.get("url")
    if url:
        return str(url)
    tickets = event.get("tickets_url")
    if tickets:
        return str(tickets)
    ticket_links = event.get("ticketLinks") or {}
    if ticket_links:
        return str(next(iter(ticket_links.values())))
    return ""


def _event_title(event: dict) -> str:
    return (
        event.get("title")
        or event.get("titleRu")
        or event.get("title_ru")
        or event.get("title_ro")
        or event.get("titleRo")
        or "Событие"
    )


def _event_description(event: dict) -> str:
    return (
        event.get("description")
        or event.get("descriptionRu")
        or event.get("description_ru")
        or event.get("description_ro")
        or event.get("descriptionRo")
        or ""
    )


def _build_message(event: dict) -> tuple[str, InlineKeyboardMarkup]:
    title = _event_title(event)
    date_raw = event.get("dateStart") or event.get("date_start")
    date_str = _format_date(date_raw)
    description = _event_description(event)[:300]
    url = _event_url(event) or "https://digest.ai"

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

    users_by_public_id = {u.public_id: u for u in User.objects.all()}
    events_by_public_id: dict[str, list[int]] = defaultdict(list)
    seen_ids: dict[str, set[int]] = defaultdict(set)

    all_recs = get_all_new_recommendations()
    for rec in all_recs:
        uid = _rec_user_id(rec)
        if not uid:
            logger.debug("Recommendation row without user id, skipping: %s", rec)
            continue
        eid = _rec_event_id(rec)
        if eid is None:
            continue
        if eid not in seen_ids[uid]:
            seen_ids[uid].add(eid)
            events_by_public_id[uid].append(eid)

    if not any(events_by_public_id.values()):
        logger.info("No new recommendation event ids in batch response")
        return

    all_ids: set[int] = set()
    for ids in events_by_public_id.values():
        all_ids.update(ids)

    events_by_id = get_events_by_ids(list(all_ids))
    missing = all_ids - {int(k) for k in events_by_id if k.isdigit()}
    for mid in missing:
        logger.warning("Parser omitted or inactive event id=%s", mid)

    for public_id, event_ids in events_by_public_id.items():
        user = users_by_public_id.get(public_id)
        if not user:
            logger.warning("No tg user found for public_id=%s", public_id)
            continue

        fresh_events = [events_by_id[str(i)] for i in event_ids if str(i) in events_by_id]
        if not fresh_events:
            continue

        try:
            asyncio.run(_send_events(user.telegram_id, fresh_events))
            logger.info("Sent %d events to telegram_id=%s", len(fresh_events), user.telegram_id)
        except Exception:
            logger.exception("Failed to send digest to telegram_id=%s", user.telegram_id)

    logger.info("Morning digest job completed")
