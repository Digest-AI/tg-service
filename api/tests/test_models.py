from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from api.models import VerificationCode


class VerificationCodeModelTests(TestCase):
    def test_code_auto_generated_on_save(self):
        code = VerificationCode(username="user", telegram_id="123")
        code.save()
        self.assertIsNotNone(code.code)
        self.assertEqual(len(code.code), 6)

    def test_expires_at_auto_set_to_10_minutes(self):
        before = timezone.now()
        code = VerificationCode(username="user", telegram_id="123")
        code.save()
        self.assertGreater(code.expires_at, before + timedelta(minutes=9))
        self.assertLess(code.expires_at, before + timedelta(minutes=11))

    def test_code_not_overridden_on_update(self):
        code = VerificationCode(username="user", telegram_id="123")
        code.save()
        original = code.code
        code.username = "updated"
        code.save()
        self.assertEqual(code.code, original)

    def test_is_expired_false_for_fresh_code(self):
        code = VerificationCode(username="user", telegram_id="123")
        code.save()
        self.assertFalse(code.is_expired)

    def test_is_expired_true_for_expired_code(self):
        code = VerificationCode(username="user", telegram_id="123")
        code.save()
        VerificationCode.objects.filter(pk=code.pk).update(
            expires_at=timezone.now() - timedelta(minutes=1)
        )
        code.refresh_from_db()
        self.assertTrue(code.is_expired)

    def test_generated_codes_are_unique(self):
        codes = {
            VerificationCode.objects.create(username=f"user{i}", telegram_id=str(i)).code
            for i in range(10)
        }
        self.assertEqual(len(codes), 10)

    def test_code_uses_allowed_alphabet(self):
        _ALPHABET = set("ABCDEFGHJKLMNPQRSTUVWXYZ23456789")
        code = VerificationCode(username="user", telegram_id="123")
        code.save()
        self.assertTrue(all(c in _ALPHABET for c in code.code))
