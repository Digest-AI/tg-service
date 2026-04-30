import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


def start_scheduler() -> None:
    from jobs.morning_digest import morning_digest_job

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        morning_digest_job,
        CronTrigger(hour=10, minute=0, timezone="UTC"),
        id="morning_digest",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started — morning digest fires at 10:00 UTC daily")
