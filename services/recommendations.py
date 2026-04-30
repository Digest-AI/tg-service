import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def get_all_new_recommendations() -> list[dict]:
    """Fetch all new recommendations across all users from recommendations-service.

    Returns a flat list of recommendation objects, each containing:
      - publicId (str): the user's public_id
      - event (dict): event data with dateStart, dateEnd, id, url, etc.

    Does NOT trigger any state change on the recommendations-service side (is_new stays True).
    """
    try:
        response = requests.get(
            f"{settings.RECOMMENDATIONS_SERVICE_URL}/api/recommendations/",
            params={"isNew": "true"},
            headers={
                "X-Service-Id": settings.SERVICE_ID,
                "X-Service-Secret": settings.SERVICE_SECRET,
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except Exception:
        logger.exception("Failed to fetch new recommendations")
        return []
