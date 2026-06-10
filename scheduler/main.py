"""Standalone scheduler process entry point.
Run: python -m scheduler.main
Uses plain asyncio loop — avoids APScheduler compatibility issues.
"""
import asyncio
import logging
from datetime import datetime, timezone
from scheduler.tasks import run_price_crawl, run_daily_cleanup, run_daily_report
from app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("scheduler")


async def price_crawl_loop():
    """Run price crawl every crawler_interval_seconds."""
    while True:
        try:
            logger.info(f"Starting price crawl (interval={settings.crawler_interval_seconds}s)")
            await run_price_crawl()
        except Exception as e:
            logger.error(f"Price crawl failed: {e}", exc_info=True)
        await asyncio.sleep(settings.crawler_interval_seconds)


async def daily_task_loop(task, task_name: str, target_hour: int):
    """Run a task once per day at target_hour UTC."""
    while True:
        now = datetime.now(timezone.utc)
        next_run = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
        if next_run <= now:
            next_run = next_run.replace(day=now.day + 1)
        wait_seconds = (next_run - now).total_seconds()
        logger.info(f"Next {task_name} at {next_run.isoformat()} (in {wait_seconds:.0f}s)")
        await asyncio.sleep(wait_seconds)
        try:
            await task()
        except Exception as e:
            logger.error(f"{task_name} failed: {e}", exc_info=True)


async def main():
    logger.info(
        f"Scheduler started — crawl every {settings.crawler_interval_seconds}s, "
        f"cleanup at {settings.retention_cleanup_hour}:00 UTC, "
        f"report at {settings.daily_report_hour}:00 UTC"
    )

    asyncio.create_task(price_crawl_loop())
    asyncio.create_task(daily_task_loop(run_daily_cleanup, "daily_cleanup", settings.retention_cleanup_hour))
    asyncio.create_task(daily_task_loop(run_daily_report, "daily_report", settings.daily_report_hour))

    try:
        while True:
            await asyncio.sleep(60)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Shutting down scheduler...")


if __name__ == "__main__":
    asyncio.run(main())
