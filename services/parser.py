import logging

import requests
from requests import HTTPError
from django.conf import settings

logger = logging.getLogger(__name__)


def _base_url() -> str:
    return (settings.PARSER_SERVICE_URL or "").rstrip("/")


def get_events_by_daterange(date_from: str, date_to: str) -> list[dict]:
    """Fetch events from parser ``GET /api/events/`` (paginated).

    Query params per OpenAPI: ``date_from``, ``date_to``, ``page_size``.
    """
    events: list[dict] = []
    base = _base_url()
    if not base:
        return events

    url: str | None = f"{base}/api/events/"
    params: dict = {"date_from": date_from, "date_to": date_to, "page_size": 100}

    while url:
        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
        except Exception:
            logger.exception("Failed to fetch events from parser (%s)", url)
            break

        if isinstance(data, dict) and "results" in data:
            events.extend(data["results"])
            url = data.get("next")
            params = {}
        else:
            if isinstance(data, list):
                events.extend(data)
            break

    return events


def get_events_by_ids(ids: list[int]) -> dict[str, dict]:
    """Fetch events via ``POST /api/events/by-ids/`` (max 100 ids per request).

    Returns ``str(event_pk) -> event`` (EventList-shaped dicts). Unknown ids are omitted by API.
    Follows ``next`` if the response is paginated.
    """
    base = _base_url()
    if not base or not ids:
        return {}

    ordered_unique: list[int] = []
    seen: set[int] = set()
    for pk in ids:
        if pk not in seen:
            seen.add(pk)
            ordered_unique.append(pk)

    out: dict[str, dict] = {}
    endpoint = f"{base}/api/events/by-ids/"

    for i in range(0, len(ordered_unique), 100):
        chunk = ordered_unique[i : i + 100]
        try:
            response = requests.post(
                endpoint,
                json={"ids": chunk},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
        except Exception:
            logger.exception("Failed parser POST /api/events/by-ids/ (chunk size=%s)", len(chunk))
            continue

        if not isinstance(data, dict):
            logger.warning("Unexpected by-ids JSON type: %s", type(data).__name__)
            continue

        rows: list = list(data.get("results") or [])
        next_url = data.get("next")
        while next_url:
            try:
                page = requests.get(next_url, timeout=30)
                page.raise_for_status()
                pdata = page.json()
            except Exception:
                logger.exception("Failed by-ids pagination GET")
                break
            if not isinstance(pdata, dict):
                break
            rows.extend(pdata.get("results") or [])
            next_url = pdata.get("next")

        for row in rows:
            if isinstance(row, dict) and row.get("id") is not None:
                out[str(row["id"])] = row

    return out


def get_event_by_id(event_id: int) -> dict | None:
    """Fetch one event: ``GET /api/events/{id}/`` (full ``Event`` serializer)."""
    base = _base_url()
    if not base:
        return None
    url = f"{base}/api/events/{int(event_id)}/"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, dict) else None
    except HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            logger.warning("Parser 404 for event id=%s", event_id)
            return None
        logger.exception("HTTP error fetching parser event id=%s", event_id)
        return None
    except Exception:
        logger.exception("Failed to fetch parser event id=%s", event_id)
        return None
