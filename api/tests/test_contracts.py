"""
Contract tests — verify tg-service correctly handles the data shapes
it expects from recommendations-service and parser-service.

If either service changes its response format, these tests will fail
and pinpoint the breaking field before runtime.
"""
from unittest.mock import MagicMock, patch

from django.test import TestCase

from api.models import User
from jobs.morning_digest import morning_digest_job
from services.parser import get_events_by_daterange
from services.recommendations import get_all_new_recommendations

# ---------------------------------------------------------------------------
# Canonical response shapes (single source of truth for integration contract)
# ---------------------------------------------------------------------------

RECOMMENDATION_CONTRACT = {
    "publicId": "user-uuid-001",
    "event": {
        "id": "event-001",
        "dateStart": "2026-05-15T10:00:00Z",
        "title": "AI Conference Moscow",
        "description": "Leading experts discuss AI trends.",
        "url": "https://digest.ai/events/1",
    },
}

PARSER_EVENT_CONTRACT = {
    "id": "event-001",
    "dateStart": "2026-05-15T10:00:00Z",
    "dateEnd": "2026-05-15T18:00:00Z",
    "title": "AI Conference Moscow",
    "description": "Leading experts discuss AI trends in business.",
    "url": "https://digest.ai/events/1",
    "ticketLinks": {"official": "https://tickets.digest.ai/1"},
}


# ---------------------------------------------------------------------------
# Recommendations-service contract
# ---------------------------------------------------------------------------

class RecommendationsContractTests(TestCase):
    """tg-service must be able to process the recommendations-service response."""

    @patch("services.recommendations.requests.get")
    def test_accepts_canonical_response_shape(self, mock_get):
        mock_get.return_value.json.return_value = [RECOMMENDATION_CONTRACT]
        mock_get.return_value.raise_for_status = MagicMock()
        result = get_all_new_recommendations()
        self.assertEqual(len(result), 1)
        rec = result[0]
        self.assertIn("publicId", rec)
        self.assertIn("event", rec)

    @patch("services.recommendations.requests.get")
    def test_required_fields_present_in_event(self, mock_get):
        mock_get.return_value.json.return_value = [RECOMMENDATION_CONTRACT]
        mock_get.return_value.raise_for_status = MagicMock()
        result = get_all_new_recommendations()
        event = result[0]["event"]
        for field in ("id", "dateStart", "title", "url"):
            self.assertIn(field, event, msg=f"Required field '{field}' missing in event contract")

    @patch("services.recommendations.requests.get")
    def test_extra_fields_do_not_break_processing(self, mock_get):
        rec_with_extras = {**RECOMMENDATION_CONTRACT, "isNew": True, "createdAt": "2026-05-01"}
        mock_get.return_value.json.return_value = [rec_with_extras]
        mock_get.return_value.raise_for_status = MagicMock()
        result = get_all_new_recommendations()
        self.assertEqual(len(result), 1)

    @patch("jobs.morning_digest.asyncio.run")
    @patch("jobs.morning_digest.get_events_by_daterange", return_value=[])
    @patch("jobs.morning_digest.get_all_new_recommendations")
    def test_public_id_snake_case_variant_accepted(self, mock_recs, _parser, mock_run):
        """recommendations-service may return public_id instead of publicId."""
        User.objects.create(public_id="user-uuid-001", username="user1", telegram_id="111")
        snake_case_rec = {"public_id": "user-uuid-001", "event": {**RECOMMENDATION_CONTRACT["event"]}}
        mock_recs.return_value = [snake_case_rec]
        morning_digest_job()
        mock_run.assert_called_once()

    @patch("jobs.morning_digest.asyncio.run")
    @patch("jobs.morning_digest.get_events_by_daterange", return_value=[])
    @patch("jobs.morning_digest.get_all_new_recommendations")
    def test_user_id_field_variant_accepted(self, mock_recs, _parser, mock_run):
        """recommendations-service may return userId instead of publicId."""
        User.objects.create(public_id="user-uuid-001", username="user1", telegram_id="111")
        user_id_rec = {"userId": "user-uuid-001", "event": {**RECOMMENDATION_CONTRACT["event"]}}
        mock_recs.return_value = [user_id_rec]
        morning_digest_job()
        mock_run.assert_called_once()


# ---------------------------------------------------------------------------
# Parser-service contract
# ---------------------------------------------------------------------------

class ParserContractTests(TestCase):
    """tg-service must be able to process the parser-service response."""

    @patch("services.parser.requests.get")
    def test_accepts_flat_list_response(self, mock_get):
        mock_get.return_value.json.return_value = [PARSER_EVENT_CONTRACT]
        mock_get.return_value.raise_for_status = MagicMock()
        result = get_events_by_daterange("2026-05-15", "2026-05-15")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "event-001")

    @patch("services.parser.requests.get")
    def test_accepts_paginated_response(self, mock_get):
        page1 = {"results": [PARSER_EVENT_CONTRACT], "next": "http://parser/api/events/?page=2"}
        page2 = {"results": [{**PARSER_EVENT_CONTRACT, "id": "event-002"}], "next": None}
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.side_effect = [page1, page2]
        result = get_events_by_daterange("2026-05-15", "2026-05-16")
        self.assertEqual(len(result), 2)

    @patch("services.parser.requests.get")
    def test_required_fields_present_in_event(self, mock_get):
        mock_get.return_value.json.return_value = [PARSER_EVENT_CONTRACT]
        mock_get.return_value.raise_for_status = MagicMock()
        result = get_events_by_daterange("2026-05-15", "2026-05-15")
        event = result[0]
        for field in ("id", "dateStart", "title"):
            self.assertIn(field, event, msg=f"Required field '{field}' missing in parser event contract")

    @patch("jobs.morning_digest.asyncio.run")
    @patch("jobs.morning_digest.get_events_by_daterange")
    @patch("jobs.morning_digest.get_all_new_recommendations")
    def test_parser_event_enriches_recommendation_by_id(self, mock_recs, mock_parser, mock_run):
        """Parser event replaces rec event when IDs match."""
        User.objects.create(public_id="user-uuid-001", username="user1", telegram_id="111")
        mock_recs.return_value = [RECOMMENDATION_CONTRACT]
        mock_parser.return_value = [PARSER_EVENT_CONTRACT]
        morning_digest_job()
        mock_run.assert_called_once()

    @patch("jobs.morning_digest.asyncio.run")
    @patch("jobs.morning_digest.get_events_by_daterange")
    @patch("jobs.morning_digest.get_all_new_recommendations")
    def test_falls_back_to_rec_event_when_not_in_parser(self, mock_recs, mock_parser, mock_run):
        """If parser doesn't return matching event, use rec event data."""
        User.objects.create(public_id="user-uuid-001", username="user1", telegram_id="111")
        mock_recs.return_value = [RECOMMENDATION_CONTRACT]
        mock_parser.return_value = [{"id": "other-event", "dateStart": "2026-05-20"}]
        morning_digest_job()
        mock_run.assert_called_once()
