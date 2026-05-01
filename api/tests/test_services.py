from unittest.mock import MagicMock, patch

import requests
from django.test import TestCase

from services.parser import get_events_by_daterange
from services.recommendations import get_all_new_recommendations


class RecommendationsServiceTests(TestCase):
    @patch("services.recommendations.requests.get")
    def test_returns_list_on_success(self, mock_get):
        mock_get.return_value.json.return_value = [{"publicId": "uid-1", "event": {}}]
        mock_get.return_value.raise_for_status = MagicMock()
        result = get_all_new_recommendations()
        self.assertEqual(len(result), 1)

    @patch("services.recommendations.requests.get")
    def test_passes_is_new_param(self, mock_get):
        mock_get.return_value.json.return_value = []
        mock_get.return_value.raise_for_status = MagicMock()
        get_all_new_recommendations()
        call_kwargs = mock_get.call_args
        params = call_kwargs[1].get("params") or call_kwargs[0][1]
        self.assertEqual(params.get("isNew"), "true")

    @patch("services.recommendations.requests.get")
    def test_http_error_returns_empty_list(self, mock_get):
        mock_get.return_value.raise_for_status.side_effect = requests.HTTPError()
        result = get_all_new_recommendations()
        self.assertEqual(result, [])

    @patch("services.recommendations.requests.get")
    def test_timeout_returns_empty_list(self, mock_get):
        mock_get.side_effect = requests.Timeout()
        result = get_all_new_recommendations()
        self.assertEqual(result, [])

    @patch("services.recommendations.requests.get")
    def test_connection_error_returns_empty_list(self, mock_get):
        mock_get.side_effect = requests.ConnectionError()
        result = get_all_new_recommendations()
        self.assertEqual(result, [])


class ParserServiceTests(TestCase):
    @patch("services.parser.requests.get")
    def test_returns_flat_list(self, mock_get):
        events = [{"id": "1"}, {"id": "2"}]
        mock_get.return_value.json.return_value = events
        mock_get.return_value.raise_for_status = MagicMock()
        result = get_events_by_daterange("2026-05-01", "2026-05-31")
        self.assertEqual(result, events)

    @patch("services.parser.requests.get")
    def test_handles_paginated_response(self, mock_get):
        page1 = {"results": [{"id": "1"}, {"id": "2"}], "next": "http://parser/api/events/?page=2"}
        page2 = {"results": [{"id": "3"}], "next": None}
        mock_get.return_value.raise_for_status = MagicMock()
        mock_get.return_value.json.side_effect = [page1, page2]
        result = get_events_by_daterange("2026-05-01", "2026-05-31")
        self.assertEqual(len(result), 3)
        self.assertEqual(mock_get.call_count, 2)

    @patch("services.parser.requests.get")
    def test_http_error_returns_empty_list(self, mock_get):
        mock_get.return_value.raise_for_status.side_effect = requests.HTTPError()
        result = get_events_by_daterange("2026-05-01", "2026-05-31")
        self.assertEqual(result, [])

    @patch("services.parser.requests.get")
    def test_timeout_returns_empty_list(self, mock_get):
        mock_get.side_effect = requests.Timeout()
        result = get_events_by_daterange("2026-05-01", "2026-05-31")
        self.assertEqual(result, [])

    @patch("services.parser.requests.get")
    def test_passes_date_params(self, mock_get):
        mock_get.return_value.json.return_value = []
        mock_get.return_value.raise_for_status = MagicMock()
        get_events_by_daterange("2026-05-01", "2026-05-31")
        params = mock_get.call_args[1].get("params") or mock_get.call_args[0][1]
        self.assertEqual(params["date_from"], "2026-05-01")
        self.assertEqual(params["date_to"], "2026-05-31")
