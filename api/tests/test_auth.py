"""
Auth tests:
  - Outgoing: tg-service sends X-Service-Id / X-Service-Secret on every inter-service request.
  - Incoming: API endpoints reject requests without valid X-Service-Secret (403).
"""
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from api.models import User
from services.parser import get_events_by_daterange
from services.recommendations import get_all_new_recommendations

SERVICE_ID = "tg-service"
SERVICE_SECRET = "test-secret"


@override_settings(
    SERVICE_ID=SERVICE_ID,
    SERVICE_SECRET=SERVICE_SECRET,
    RECOMMENDATIONS_SERVICE_URL="http://recommendations",
    PARSER_SERVICE_URL="http://parser",
)
class OutgoingAuthHeadersTests(TestCase):
    def _ok_mock(self, payload):
        mock = MagicMock()
        mock.raise_for_status = MagicMock()
        mock.json.return_value = payload
        return mock

    @patch("services.recommendations.requests.get")
    def test_recommendations_request_sends_service_id(self, mock_get):
        mock_get.return_value = self._ok_mock([])
        get_all_new_recommendations()
        headers = mock_get.call_args[1]["headers"]
        self.assertEqual(headers["X-Service-Id"], SERVICE_ID)

    @patch("services.recommendations.requests.get")
    def test_recommendations_request_sends_service_secret(self, mock_get):
        mock_get.return_value = self._ok_mock([])
        get_all_new_recommendations()
        headers = mock_get.call_args[1]["headers"]
        self.assertEqual(headers["X-Service-Secret"], SERVICE_SECRET)

    @patch("services.recommendations.requests.get")
    def test_recommendations_request_sends_is_new_param(self, mock_get):
        mock_get.return_value = self._ok_mock([])
        get_all_new_recommendations()
        params = mock_get.call_args[1]["params"]
        self.assertEqual(params["isNew"], "true")

    @patch("services.parser.requests.get")
    def test_parser_request_sends_date_params(self, mock_get):
        mock_get.return_value = self._ok_mock([])
        get_events_by_daterange("2026-05-01", "2026-05-31")
        params = mock_get.call_args[1]["params"]
        self.assertEqual(params["date_from"], "2026-05-01")
        self.assertEqual(params["date_to"], "2026-05-31")

    @patch("services.recommendations.requests.get")
    def test_recommendations_uses_correct_base_url(self, mock_get):
        mock_get.return_value = self._ok_mock([])
        get_all_new_recommendations()
        url = mock_get.call_args[0][0]
        self.assertTrue(url.startswith("http://recommendations"))

    @patch("services.parser.requests.get")
    def test_parser_uses_correct_base_url(self, mock_get):
        mock_get.return_value = self._ok_mock([])
        get_events_by_daterange("2026-05-01", "2026-05-31")
        url = mock_get.call_args[0][0]
        self.assertTrue(url.startswith("http://parser"))


class IncomingAuthTests(TestCase):
    """API endpoints must reject requests without valid X-Service-Secret."""

    def setUp(self):
        self.anon = APIClient()
        self.authed = APIClient()
        self.authed.credentials(HTTP_X_SERVICE_SECRET=settings.SERVICE_SECRET)
        User.objects.create(public_id="uid-1", username="user1", telegram_id="111")

    def test_users_list_without_secret_returns_403(self):
        self.assertEqual(self.anon.get("/api/users/").status_code, 403)

    def test_users_list_with_wrong_secret_returns_403(self):
        self.anon.credentials(HTTP_X_SERVICE_SECRET="wrong-secret")
        self.assertEqual(self.anon.get("/api/users/").status_code, 403)

    def test_users_list_with_correct_secret_returns_200(self):
        self.assertEqual(self.authed.get("/api/users/").status_code, 200)

    def test_create_user_without_secret_returns_403(self):
        payload = {"publicId": "uid-2", "username": "user2", "telegramId": "222"}
        self.assertEqual(self.anon.post("/api/users/", payload, format="json").status_code, 403)

    def test_verify_code_without_secret_returns_403(self):
        response = self.anon.post(
            "/api/verification-codes/verify/",
            {"code": "AAAAAA", "publicId": "uid-x"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_webhook_does_not_require_secret(self):
        """Webhook comes from Telegram — must be accessible without service secret."""
        response = self.anon.post(
            "/api/webhook/",
            b"invalid body",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
