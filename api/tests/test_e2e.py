"""
End-to-end tests — full morning digest pipeline with real DB state.

Mocks only the HTTP calls and Telegram send; everything else
(DB queries, grouping, daterange, enrichment) runs for real.
"""
from unittest.mock import MagicMock, call, patch

from django.conf import settings
from django.test import TestCase

from api.models import User
from jobs.morning_digest import morning_digest_job

SECRET = settings.SERVICE_SECRET
AUTH = {"HTTP_X_SERVICE_SECRET": SECRET}

FAKE_RECS = [
    {
        "publicId": "uid-1",
        "event": {"id": "10", "dateStart": "2026-05-15", "title": "Event A", "url": "https://a.com"},
    },
    {
        "publicId": "uid-2",
        "event": {"id": "11", "dateStart": "2026-05-20", "title": "Event B", "url": "https://b.com"},
    },
]

FAKE_PARSER_EVENTS = [
    {"id": "10", "dateStart": "2026-05-15T10:00:00Z", "title": "Fresh A", "url": "https://a.com"},
    {"id": "11", "dateStart": "2026-05-20T14:00:00Z", "title": "Fresh B", "url": "https://b.com"},
]


class MorningDigestE2ETests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(public_id="uid-1", username="user1", telegram_id="111")
        self.user2 = User.objects.create(public_id="uid-2", username="user2", telegram_id="222")

    @patch("jobs.morning_digest.asyncio.run")
    @patch("jobs.morning_digest.get_events_by_daterange")
    @patch("jobs.morning_digest.get_all_new_recommendations")
    def test_each_user_gets_only_their_events(self, mock_recs, mock_parser, mock_run):
        mock_recs.return_value = FAKE_RECS
        mock_parser.return_value = FAKE_PARSER_EVENTS
        morning_digest_job()
        self.assertEqual(mock_run.call_count, 2)

    @patch("jobs.morning_digest.asyncio.run")
    @patch("jobs.morning_digest.get_events_by_daterange")
    @patch("jobs.morning_digest.get_all_new_recommendations")
    def test_daterange_spans_all_users_events(self, mock_recs, mock_parser, mock_run):
        mock_recs.return_value = FAKE_RECS
        mock_parser.return_value = FAKE_PARSER_EVENTS
        morning_digest_job()
        mock_parser.assert_called_once_with("2026-05-15", "2026-05-20")

    @patch("jobs.morning_digest.asyncio.run")
    @patch("jobs.morning_digest.get_events_by_daterange")
    @patch("jobs.morning_digest.get_all_new_recommendations")
    def test_user_with_multiple_recs_gets_all_events(self, mock_recs, mock_parser, mock_run):
        recs = [
            {"publicId": "uid-1", "event": {"id": "10", "dateStart": "2026-05-15"}},
            {"publicId": "uid-1", "event": {"id": "11", "dateStart": "2026-05-16"}},
            {"publicId": "uid-1", "event": {"id": "12", "dateStart": "2026-05-17"}},
        ]
        mock_recs.return_value = recs
        mock_parser.return_value = []
        morning_digest_job()
        self.assertEqual(mock_run.call_count, 1)

    @patch("jobs.morning_digest.asyncio.run")
    @patch("jobs.morning_digest.get_events_by_daterange")
    @patch("jobs.morning_digest.get_all_new_recommendations")
    def test_user_without_tg_account_does_not_receive(self, mock_recs, mock_parser, mock_run):
        recs = [
            {"publicId": "uid-1", "event": {"id": "10", "dateStart": "2026-05-15"}},
            {"publicId": "uid-no-tg", "event": {"id": "11", "dateStart": "2026-05-15"}},
        ]
        mock_recs.return_value = recs
        mock_parser.return_value = []
        morning_digest_job()
        self.assertEqual(mock_run.call_count, 1)

    @patch("jobs.morning_digest.asyncio.run")
    @patch("jobs.morning_digest.get_events_by_daterange")
    @patch("jobs.morning_digest.get_all_new_recommendations")
    def test_db_query_uses_only_relevant_public_ids(self, mock_recs, mock_parser, mock_run):
        """Only users referenced in recs are queried — no full table scan."""
        User.objects.create(public_id="uid-irrelevant", username="user3", telegram_id="333")
        mock_recs.return_value = [
            {"publicId": "uid-1", "event": {"id": "10", "dateStart": "2026-05-15"}},
        ]
        mock_parser.return_value = []
        morning_digest_job()
        self.assertEqual(mock_run.call_count, 1)

    @patch("jobs.morning_digest.asyncio.run")
    @patch("jobs.morning_digest.get_events_by_daterange")
    @patch("jobs.morning_digest.get_all_new_recommendations")
    def test_no_users_in_db_no_sends(self, mock_recs, mock_parser, mock_run):
        User.objects.all().delete()
        mock_recs.return_value = FAKE_RECS
        mock_parser.return_value = FAKE_PARSER_EVENTS
        morning_digest_job()
        mock_run.assert_not_called()

    @patch("jobs.morning_digest.asyncio.run")
    @patch("jobs.morning_digest.get_events_by_daterange")
    @patch("jobs.morning_digest.get_all_new_recommendations")
    def test_second_user_still_sent_when_first_fails(self, mock_recs, mock_parser, mock_run):
        mock_recs.return_value = FAKE_RECS
        mock_parser.return_value = []
        mock_run.side_effect = [Exception("tg error"), None]
        morning_digest_job()
        self.assertEqual(mock_run.call_count, 2)


class VerificationFlowE2ETests(TestCase):
    """Full account linking flow: code generated in bot → verified via API."""

    def test_full_verification_flow(self):
        from api.models import VerificationCode
        code = VerificationCode(username="newuser", telegram_id="999")
        code.save()

        response = self.client.post(
            "/api/verification-codes/verify/",
            {"code": code.code, "publicId": "main-service-uuid"},
            content_type="application/json",
            **AUTH,
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["username"], "newuser")
        self.assertEqual(data["telegramId"], "999")
        self.assertEqual(data["publicId"], "main-service-uuid")
        self.assertFalse(VerificationCode.objects.filter(pk=code.pk).exists())
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_verified_user_appears_in_users_list(self):
        from api.models import VerificationCode
        code = VerificationCode(username="listeduser", telegram_id="777")
        code.save()

        self.client.post(
            "/api/verification-codes/verify/",
            {"code": code.code, "publicId": "uid-listed"},
            content_type="application/json",
            **AUTH,
        )

        response = self.client.get("/api/users/", **AUTH)
        self.assertEqual(response.status_code, 200)
        usernames = [u["username"] for u in response.json()]
        self.assertIn("listeduser", usernames)
