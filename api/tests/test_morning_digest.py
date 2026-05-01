from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase

from api.models import User
from jobs.morning_digest import _LOCK_KEY, _event_url, _format_date, morning_digest_job


class FormatDateTests(TestCase):
    def test_none_returns_default(self):
        self.assertEqual(_format_date(None), "Дата уточняется")

    def test_iso_utc(self):
        self.assertEqual(_format_date("2026-05-15T10:00:00Z"), "15.05.2026 10:00")

    def test_iso_with_offset(self):
        self.assertEqual(_format_date("2026-05-15T10:00:00+03:00"), "15.05.2026 10:00")

    def test_invalid_string_returned_as_is(self):
        self.assertEqual(_format_date("not-a-date"), "not-a-date")


class EventUrlTests(TestCase):
    def test_url_field(self):
        self.assertEqual(_event_url({"url": "https://example.com"}), "https://example.com")

    def test_ticket_links_fallback(self):
        self.assertEqual(
            _event_url({"ticketLinks": {"site": "https://tickets.com"}}),
            "https://tickets.com",
        )

    def test_url_takes_priority_over_ticket_links(self):
        self.assertEqual(
            _event_url({"url": "https://direct.com", "ticketLinks": {"site": "https://tickets.com"}}),
            "https://direct.com",
        )

    def test_empty_event_returns_empty_string(self):
        self.assertEqual(_event_url({}), "")


class MorningDigestJobTests(TestCase):
    @patch("jobs.morning_digest.get_all_new_recommendations", return_value=[])
    def test_no_recommendations_skips_parser(self, _mock_recs):
        with patch("jobs.morning_digest.get_events_by_daterange") as mock_parser:
            morning_digest_job()
            mock_parser.assert_not_called()

    @patch("jobs.morning_digest.get_all_new_recommendations")
    def test_recs_without_event_field_skips_parser(self, mock_recs):
        mock_recs.return_value = [{"publicId": "uid-1"}]
        with patch("jobs.morning_digest.get_events_by_daterange") as mock_parser:
            morning_digest_job()
            mock_parser.assert_not_called()

    @patch("jobs.morning_digest.get_all_new_recommendations")
    def test_recs_without_dates_skips_parser(self, mock_recs):
        mock_recs.return_value = [{"publicId": "uid-1", "event": {"id": "10"}}]
        with patch("jobs.morning_digest.get_events_by_daterange") as mock_parser:
            morning_digest_job()
            mock_parser.assert_not_called()

    @patch("jobs.morning_digest.asyncio.run")
    @patch("jobs.morning_digest.get_events_by_daterange", return_value=[])
    @patch("jobs.morning_digest.get_all_new_recommendations")
    def test_daterange_uses_min_and_max_dates(self, mock_recs, mock_parser, _mock_run):
        User.objects.create(public_id="uid-1", username="user1", telegram_id="111")
        mock_recs.return_value = [
            {"publicId": "uid-1", "event": {"id": "1", "dateStart": "2026-06-01"}},
            {"publicId": "uid-1", "event": {"id": "2", "dateStart": "2026-06-15"}},
            {"publicId": "uid-1", "event": {"id": "3", "dateStart": "2026-05-20"}},
        ]
        morning_digest_job()
        mock_parser.assert_called_once_with("2026-05-20", "2026-06-15")

    @patch("jobs.morning_digest.asyncio.run")
    @patch("jobs.morning_digest.get_events_by_daterange")
    @patch("jobs.morning_digest.get_all_new_recommendations")
    def test_normal_flow_calls_send_once_per_user(self, mock_recs, mock_parser, mock_run):
        User.objects.create(public_id="uid-1", username="user1", telegram_id="111")
        User.objects.create(public_id="uid-2", username="user2", telegram_id="222")
        mock_recs.return_value = [
            {"publicId": "uid-1", "event": {"id": "10", "dateStart": "2026-05-15"}},
            {"publicId": "uid-2", "event": {"id": "11", "dateStart": "2026-05-16"}},
        ]
        mock_parser.return_value = []
        morning_digest_job()
        self.assertEqual(mock_run.call_count, 2)

    @patch("jobs.morning_digest.asyncio.run")
    @patch("jobs.morning_digest.get_events_by_daterange", return_value=[])
    @patch("jobs.morning_digest.get_all_new_recommendations")
    def test_unknown_public_id_skips_send(self, mock_recs, _mock_parser, mock_run):
        mock_recs.return_value = [
            {"publicId": "unknown-uid", "event": {"id": "10", "dateStart": "2026-05-15"}},
        ]
        morning_digest_job()
        mock_run.assert_not_called()

    @patch("jobs.morning_digest.asyncio.run")
    @patch("jobs.morning_digest.get_events_by_daterange", return_value=[])
    @patch("jobs.morning_digest.get_all_new_recommendations")
    def test_send_failure_does_not_stop_other_users(self, mock_recs, _mock_parser, mock_run):
        User.objects.create(public_id="uid-1", username="user1", telegram_id="111")
        User.objects.create(public_id="uid-2", username="user2", telegram_id="222")
        mock_recs.return_value = [
            {"publicId": "uid-1", "event": {"id": "10", "dateStart": "2026-05-15"}},
            {"publicId": "uid-2", "event": {"id": "11", "dateStart": "2026-05-16"}},
        ]
        mock_run.side_effect = [Exception("send failed"), None]
        morning_digest_job()
        self.assertEqual(mock_run.call_count, 2)

    @patch("jobs.morning_digest.asyncio.run")
    @patch("jobs.morning_digest.get_events_by_daterange")
    @patch("jobs.morning_digest.get_all_new_recommendations")
    def test_parser_event_enriches_rec_event(self, mock_recs, mock_parser, mock_run):
        User.objects.create(public_id="uid-1", username="user1", telegram_id="111")
        mock_recs.return_value = [
            {"publicId": "uid-1", "event": {"id": "10", "dateStart": "2026-05-15", "title": "Old"}},
        ]
        fresh = {"id": "10", "dateStart": "2026-05-15T10:00:00Z", "title": "Fresh", "url": "https://x.com"}
        mock_parser.return_value = [fresh]
        morning_digest_job()
        mock_run.assert_called_once()

    @patch("jobs.morning_digest.asyncio.run")
    @patch("jobs.morning_digest.get_events_by_daterange", return_value=[])
    @patch("jobs.morning_digest.get_all_new_recommendations")
    def test_accepts_public_id_field_variants(self, mock_recs, _mock_parser, mock_run):
        User.objects.create(public_id="uid-1", username="user1", telegram_id="111")
        mock_recs.return_value = [
            {"public_id": "uid-1", "event": {"id": "10", "dateStart": "2026-05-15"}},
        ]
        morning_digest_job()
        mock_run.assert_called_once()


class DigestLockTests(TestCase):
    def tearDown(self):
        cache.delete(_LOCK_KEY)

    @patch("jobs.morning_digest.get_all_new_recommendations", return_value=[])
    def test_second_call_is_skipped_while_lock_held(self, mock_recs):
        cache.add(_LOCK_KEY, True, 3600)
        morning_digest_job()
        mock_recs.assert_not_called()

    @patch("jobs.morning_digest.get_all_new_recommendations", return_value=[])
    def test_lock_released_after_job_completes(self, _mock_recs):
        morning_digest_job()
        self.assertIsNone(cache.get(_LOCK_KEY))

    @patch("jobs.morning_digest.get_all_new_recommendations")
    def test_lock_released_even_on_exception(self, mock_recs):
        mock_recs.side_effect = Exception("unexpected crash")
        try:
            morning_digest_job()
        except Exception:
            pass
        self.assertIsNone(cache.get(_LOCK_KEY))

    @patch("jobs.morning_digest.get_all_new_recommendations", return_value=[])
    def test_second_call_runs_after_lock_released(self, mock_recs):
        morning_digest_job()
        morning_digest_job()
        self.assertEqual(mock_recs.call_count, 2)
