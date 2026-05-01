from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import User, VerificationCode

SECRET = settings.SERVICE_SECRET


def _make_code(username="testuser", telegram_id="123456789") -> VerificationCode:
    code = VerificationCode(username=username, telegram_id=telegram_id)
    code.save()
    return code


def _make_expired_code(username="testuser", telegram_id="123456789") -> VerificationCode:
    code = _make_code(username, telegram_id)
    VerificationCode.objects.filter(pk=code.pk).update(
        expires_at=timezone.now() - timedelta(minutes=1)
    )
    return VerificationCode.objects.get(pk=code.pk)


class VerifyCodeTests(APITestCase):
    url = "/api/verification-codes/verify/"

    def setUp(self):
        self.client.credentials(HTTP_X_SERVICE_SECRET=SECRET)

    def test_verify_valid_code_creates_user(self):
        code = _make_code()
        response = self.client.post(
            self.url,
            {"code": code.code, "publicId": "uid-1"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertEqual(data["username"], "testuser")
        self.assertEqual(data["telegramId"], "123456789")
        self.assertEqual(data["publicId"], "uid-1")
        self.assertEqual(User.objects.count(), 1)
        self.assertFalse(VerificationCode.objects.filter(pk=code.pk).exists())

    def test_verify_code_lowercase_accepted(self):
        code = _make_code()
        response = self.client.post(
            self.url,
            {"code": code.code.lower(), "publicId": "uid-1"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_verify_invalid_code(self):
        response = self.client.post(
            self.url,
            {"code": "XXXXXX", "publicId": "uid-1"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(User.objects.count(), 0)

    def test_verify_expired_code(self):
        code = _make_expired_code()
        response = self.client.post(
            self.url,
            {"code": code.code, "publicId": "uid-1"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(VerificationCode.objects.filter(pk=code.pk).exists())
        self.assertEqual(User.objects.count(), 0)

    def test_verify_code_already_linked_returns_existing_user(self):
        User.objects.create(
            public_id="uid-existing",
            username="testuser",
            telegram_id="123456789",
        )
        code = _make_code()
        response = self.client.post(
            self.url,
            {"code": code.code, "publicId": "uid-new"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(response.json()["publicId"], "uid-existing")

    def test_verify_missing_code_field(self):
        response = self.client.post(self.url, {"publicId": "uid-1"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_missing_public_id_field(self):
        code = _make_code()
        response = self.client.post(self.url, {"code": code.code}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
