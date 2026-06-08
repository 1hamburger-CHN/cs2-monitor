"""Standalone scheduler process entry point.
Run: python -m scheduler.main
Managed by systemd, separate from the web server.
"""
import asyncio
import logging
from apscheduler import AsyncScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from scheduler.tasks import run_price_crawl, run_daily_cleanup, run_daily_report
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("scheduler")


async def main():
    scheduler = AsyncScheduler()

    # Price crawl + alert every N seconds
    await scheduler.add_schedule(
        run_price_crawl,
        IntervalTrigger(seconds=settings.crawler_interval_seconds),
        id="price_crawl",
    )

    # Daily cleanup at configured hour
    await scheduler.add_schedule(
        run_daily_cleanup,
        CronTrigger(hour=settings.retention_cleanup_hour, minute=0),
        id="daily_cleanup",
    )

    # Daily report at configured hour
    await scheduler.add_schedule(
        run_daily_report,
        CronTrigger(hour=settings.daily_report_hour, minute=0),
        id="daily_report",
    )

    await scheduler.start_in_background()
    logger.info(
        f"Scheduler started — crawl every {settings.crawler_interval_seconds}s, "
        f"cleanup at {settings.retention_cleanup_hour}:00, "
        f"report at {settings.daily_report_hour}:00"
    )

    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Shutting down scheduler...")
        await scheduler.stop()


if __name__ == "__main__":
    asyncio.run(main())
