import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def _base_url() -> str:
    return (settings.RECOMMENDATIONS_SERVICE_URL or "").rstrip("/")


def _service_headers() -> dict[str, str]:
    sid = getattr(settings, "SERVICE_ID", None) or ""
    secret = getattr(settings, "SERVICE_SECRET", None) or ""
    if not sid or not secret:
        return {}
    return {"X-Service-Id": sid, "X-Service-Secret": secret}


def get_all_new_recommendations() -> list[dict]:
    """``GET /api/recommendations/new/`` без ``user_id`` — все новые рекомендации сразу.

    В каждой строке ожидаются как минимум ``event_id`` и идентификатор пользователя
    (``user_id`` / ``userId`` или ``public_id`` / ``publicId``).
    """
    base = _base_url()
    if not base:
        return []
    try:
        response = requests.get(
            f"{base}/api/recommendations/new/",
            headers=_service_headers(),
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else []
    except Exception:
        logger.exception("Failed to fetch all new recommendations")
        return []
