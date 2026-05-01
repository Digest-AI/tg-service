import asyncio
from unittest.mock import AsyncMock, patch

from django.test import TransactionTestCase

from api.models import User
from middlewares.check_linked import CheckLinkedMiddleware


def _make_message(text: str, username: str | None = "testuser"):
    from aiogram.types import Message
    return Message.model_validate({
        "message_id": 1,
        "date": 1234567890,
        "chat": {"id": 123, "type": "private"},
        "from": {"id": 456, "is_bot": False, "first_name": "Test", "username": username},
        "text": text,
    })


class CheckLinkedMiddlewareTests(TransactionTestCase):
    def setUp(self):
        self.middleware = CheckLinkedMiddleware()

    def test_start_command_passes_unlinked_user(self):
        msg = _make_message("/start")
        handler = AsyncMock(return_value="ok")
        result = asyncio.run(self.middleware(handler, msg, {}))
        self.assertEqual(result, "ok")
        handler.assert_called_once()

    def test_help_command_passes_unlinked_user(self):
        msg = _make_message("/help")
        handler = AsyncMock(return_value="ok")
        result = asyncio.run(self.middleware(handler, msg, {}))
        self.assertEqual(result, "ok")

    def test_premium_command_passes_unlinked_user(self):
        msg = _make_message("/premium")
        handler = AsyncMock(return_value="ok")
        result = asyncio.run(self.middleware(handler, msg, {}))
        self.assertEqual(result, "ok")

    def test_linked_user_passes_through(self):
        User.objects.create(public_id="uid-1", username="testuser", telegram_id="123")
        msg = _make_message("Hello")
        handler = AsyncMock(return_value="ok")
        with patch("aiogram.types.Message.answer", new_callable=AsyncMock):
            result = asyncio.run(self.middleware(handler, msg, {}))
        self.assertEqual(result, "ok")
        handler.assert_called_once()

    def test_unlinked_user_is_blocked(self):
        msg = _make_message("Hello")
        handler = AsyncMock()
        with patch("aiogram.types.Message.answer", new_callable=AsyncMock) as mock_answer:
            result = asyncio.run(self.middleware(handler, msg, {}))
        self.assertIsNone(result)
        handler.assert_not_called()
        mock_answer.assert_called_once()

    def test_message_without_username_is_blocked(self):
        msg = _make_message("Hello", username=None)
        handler = AsyncMock()
        with patch("aiogram.types.Message.answer", new_callable=AsyncMock) as mock_answer:
            result = asyncio.run(self.middleware(handler, msg, {}))
        self.assertIsNone(result)
        handler.assert_not_called()
        mock_answer.assert_called_once()

    def test_non_message_event_passes_through(self):
        event = object()
        handler = AsyncMock(return_value="ok")
        result = asyncio.run(self.middleware(handler, event, {}))
        self.assertEqual(result, "ok")
