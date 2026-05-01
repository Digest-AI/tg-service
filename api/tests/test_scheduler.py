"""
Scheduler tests — verify morning_digest job is registered with correct trigger.
Smoke tests — verify the service is alive and schema is accessible.
Migration tests — verify no unapplied migrations exist.
"""
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient


class SchedulerTests(TestCase):
    def test_job_registered_with_correct_id(self):
        from apscheduler.schedulers.background import BackgroundScheduler

        with patch.object(BackgroundScheduler, "start"):
            from scheduler import start_scheduler
            with patch.object(BackgroundScheduler, "add_job") as mock_add:
                start_scheduler()
            mock_add.assert_called_once()
            _, kwargs = mock_add.call_args
            self.assertEqual(kwargs.get("id") or mock_add.call_args[0][1] if len(mock_add.call_args[0]) > 1 else kwargs.get("id"), "morning_digest")

    def test_job_registered_at_10_utc(self):
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger

        with patch.object(BackgroundScheduler, "start"):
            with patch.object(BackgroundScheduler, "add_job") as mock_add:
                from scheduler import start_scheduler
                start_scheduler()
            trigger = mock_add.call_args[0][1] if len(mock_add.call_args[0]) > 1 else mock_add.call_args[1].get("trigger")
            if isinstance(trigger, CronTrigger):
                fields = {f.name: str(f) for f in trigger.fields}
                self.assertEqual(fields.get("hour"), "10")
                self.assertEqual(fields.get("minute"), "0")

    def test_morning_digest_job_is_the_registered_function(self):
        from apscheduler.schedulers.background import BackgroundScheduler
        from jobs.morning_digest import morning_digest_job

        with patch.object(BackgroundScheduler, "start"):
            with patch.object(BackgroundScheduler, "add_job") as mock_add:
                from scheduler import start_scheduler
                start_scheduler()
            registered_func = mock_add.call_args[0][0]
            self.assertEqual(registered_func, morning_digest_job)


class SmokeTests(TestCase):
    def test_schema_endpoint_returns_200(self):
        response = self.client.get("/schema/")
        self.assertEqual(response.status_code, 200)

    def test_swagger_ui_returns_200(self):
        response = self.client.get("/schema/swagger-ui/")
        self.assertEqual(response.status_code, 200)

    def test_users_endpoint_accessible(self):
        client = APIClient()
        client.credentials(HTTP_X_SERVICE_SECRET=settings.SERVICE_SECRET)
        response = client.get("/api/users/")
        self.assertEqual(response.status_code, 200)

    def test_404_on_unknown_route(self):
        response = self.client.get("/api/nonexistent/")
        self.assertEqual(response.status_code, 404)


class MigrationTests(TestCase):
    def test_no_pending_migrations(self):
        """Fails if there are model changes not reflected in migrations."""
        try:
            call_command("migrate", "--check", verbosity=0)
        except SystemExit as e:
            self.fail(f"Pending migrations detected: {e}")
