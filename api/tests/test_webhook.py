"""
Webhook tests — verify POST /api/webhook/ always returns 200 to Telegram.
Non-200 causes Telegram to retry indefinitely.
"""
import json
from unittest.mock import AsyncMock, patch

from django.test import TestCase

VALID_UPDATE = {
    "update_id": 1,
    "message": {
        "message_id": 1,
        "from": {"id": 123, "is_bot": False, "first_name": "Test", "username": "testuser"},
        "chat": {"id": 123, "type": "private"},
        "date": 1234567890,
        "text": "/start",
    },
}


class TelegramWebhookTests(TestCase):
    url = "/api/webhook/"

    def _post(self, body):
        return self.client.post(
            self.url,
            data=body if isinstance(body, bytes) else json.dumps(body).encode(),
            content_type="application/json",
        )

    @patch("api.views.webhook.async_to_sync")
    def test_valid_update_returns_200(self, mock_sync):
        mock_sync.return_value = lambda: None
        response = self._post(VALID_UPDATE)
        self.assertEqual(response.status_code, 200)

    def test_invalid_json_returns_200(self):
        response = self._post(b"not valid json{{{")
        self.assertEqual(response.status_code, 200)

    def test_empty_body_returns_200(self):
        response = self._post(b"")
        self.assertEqual(response.status_code, 200)

    def test_valid_json_missing_update_id_returns_200(self):
        response = self._post({"message": "hello"})
        self.assertEqual(response.status_code, 200)

    def test_empty_json_object_returns_200(self):
        response = self._post({})
        self.assertEqual(response.status_code, 200)

    def test_get_method_not_allowed(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
