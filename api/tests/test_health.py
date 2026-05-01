"""
Health / resilience tests — verify tg-service degrades gracefully
when recommendations-service or parser-service are unavailable.
"""
from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase

from api.models import User
from jobs.morning_digest import morning_digest_job


class RecommendationsServiceDownTests(TestCase):
    def setUp(self):
        User.objects.create(public_id="uid-1", username="user1", telegram_id="111")

    @patch("jobs.morning_digest.get_all_new_recommendations", return_value=[])
    def test_no_recs_returned_no_sends(self, _mock):
        with patch("jobs.morning_digest.asyncio.run") as mock_run:
            morning_digest_job()
        mock_run.assert_not_called()

    @patch("services.recommendations.requests.get")
    def test_http_500_returns_empty_list(self, mock_get):
        from services.recommendations import get_all_new_recommendations
        mock_get.return_value.raise_for_status.side_effect = requests.HTTPError(
            response=MagicMock(status_code=500)
        )
        result = get_all_new_recommendations()
        self.assertEqual(result, [])

    @patch("services.recommendations.requests.get")
    def test_timeout_returns_empty_list(self, mock_get):
        from services.recommendations import get_all_new_recommendations
        mock_get.side_effect = requests.Timeout()
        result = get_all_new_recommendations()
        self.assertEqual(result, [])

    @patch("services.recommendations.requests.get")
    def test_connection_refused_returns_empty_list(self, mock_get):
        from services.recommendations import get_all_new_recommendations
        mock_get.side_effect = requests.ConnectionError()
        result = get_all_new_recommendations()
        self.assertEqual(result, [])


class ParserServiceDownTests(TestCase):
    def setUp(self):
        User.objects.create(public_id="uid-1", username="user1", telegram_id="111")

    @patch("services.parser.requests.get")
    def test_http_500_returns_empty_list(self, mock_get):
        from services.parser import get_events_by_daterange
        mock_get.return_value.raise_for_status.side_effect = requests.HTTPError(
            response=MagicMock(status_code=500)
        )
        result = get_events_by_daterange("2026-05-01", "2026-05-31")
        self.assertEqual(result, [])

    @patch("services.parser.requests.get")
    def test_timeout_returns_empty_list(self, mock_get):
        from services.parser import get_events_by_daterange
        mock_get.side_effect = requests.Timeout()
        result = get_events_by_daterange("2026-05-01", "2026-05-31")
        self.assertEqual(result, [])

    @patch("jobs.morning_digest.asyncio.run")
    @patch("jobs.morning_digest.get_events_by_daterange", return_value=[])
    @patch("jobs.morning_digest.get_all_new_recommendations")
    def test_parser_down_still_sends_with_rec_event_data(self, mock_recs, _parser, mock_run):
        """When parser returns nothing, fall back to event data from recommendations."""
        mock_recs.return_value = [
            {"publicId": "uid-1", "event": {"id": "10", "dateStart": "2026-05-15", "title": "Event A"}},
        ]
        morning_digest_job()
        mock_run.assert_called_once()


class BothServicesDownTests(TestCase):
    def setUp(self):
        User.objects.create(public_id="uid-1", username="user1", telegram_id="111")

    @patch("services.recommendations.requests.get")
    def test_both_down_no_exception_raised(self, mock_recs_get):
        from services.recommendations import get_all_new_recommendations
        from services.parser import get_events_by_daterange
        mock_recs_get.side_effect = requests.ConnectionError()

        with patch("services.parser.requests.get") as mock_parser_get:
            mock_parser_get.side_effect = requests.ConnectionError()
            with patch("jobs.morning_digest.get_all_new_recommendations", return_value=[]):
                with patch("jobs.morning_digest.asyncio.run") as mock_run:
                    try:
                        morning_digest_job()
                    except Exception as e:
                        self.fail(f"morning_digest_job raised an exception: {e}")
        mock_run.assert_not_called()

    @patch("jobs.morning_digest.asyncio.run")
    @patch("jobs.morning_digest.get_events_by_daterange", return_value=[])
    @patch("jobs.morning_digest.get_all_new_recommendations", return_value=[])
    def test_both_down_job_completes_silently(self, _recs, _parser, mock_run):
        morning_digest_job()
        mock_run.assert_not_called()


class TelegramSendFailureTests(TestCase):
    def setUp(self):
        User.objects.create(public_id="uid-1", username="user1", telegram_id="111")
        User.objects.create(public_id="uid-2", username="user2", telegram_id="222")
        User.objects.create(public_id="uid-3", username="user3", telegram_id="333")

    @patch("jobs.morning_digest.asyncio.run")
    @patch("jobs.morning_digest.get_events_by_daterange", return_value=[])
    @patch("jobs.morning_digest.get_all_new_recommendations")
    def test_one_failed_send_does_not_stop_others(self, mock_recs, _parser, mock_run):
        mock_recs.return_value = [
            {"publicId": "uid-1", "event": {"id": "1", "dateStart": "2026-05-15"}},
            {"publicId": "uid-2", "event": {"id": "2", "dateStart": "2026-05-15"}},
            {"publicId": "uid-3", "event": {"id": "3", "dateStart": "2026-05-15"}},
        ]
        mock_run.side_effect = [Exception("flood control"), None, None]
        morning_digest_job()
        self.assertEqual(mock_run.call_count, 3)

    @patch("jobs.morning_digest.asyncio.run")
    @patch("jobs.morning_digest.get_events_by_daterange", return_value=[])
    @patch("jobs.morning_digest.get_all_new_recommendations")
    def test_all_sends_fail_no_exception_propagated(self, mock_recs, _parser, mock_run):
        mock_recs.return_value = [
            {"publicId": "uid-1", "event": {"id": "1", "dateStart": "2026-05-15"}},
        ]
        mock_run.side_effect = Exception("tg down")
        try:
            morning_digest_job()
        except Exception as e:
            self.fail(f"morning_digest_job raised an exception: {e}")
