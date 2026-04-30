import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def get_events_by_daterange(date_from: str, date_to: str) -> list[dict]:
    """Fetch all events from parser-service within the given date range.

    Handles pagination automatically. date_from and date_to are YYYY-MM-DD strings.
    Returns camelCase event dicts as returned by the parser.
    """
    events: list[dict] = []
    url = f"{settings.PARSER_SERVICE_URL}/api/events/"
    params: dict = {"date_from": date_from, "date_to": date_to, "pageSize": 100}

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
            events.extend(data)
            break

    return events
