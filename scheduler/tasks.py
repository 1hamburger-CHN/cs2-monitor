"""Scheduled task orchestration — crawl, alert, cleanup, daily report."""
import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import WatchlistItem, User, PriceSnapshot, AlertLog
from scheduler.crawlers import csqaq
from scheduler.alerter import check_mode_1, check_mode_2
from scheduler.notifier import send_notification, format_price_alert
from scheduler.web_push import send_web_push

logger = logging.getLogger(__name__)
IMG_CACHE_FILE = Path("data/img_cache.json")


def _update_img_cache(prices: dict):
    """Persist img_url from CSQAQ results to JSON cache."""
    try:
        cache = {}
        if IMG_CACHE_FILE.exists():
            cache = json.loads(IMG_CACHE_FILE.read_text())
        for name, data in prices.items():
            if data and data.get("img_url"):
                cache[name] = data["img_url"]
        IMG_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        IMG_CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2))
    except Exception as e:
        logger.warning(f"Failed to update img cache: {e}")


async def run_price_crawl():
    """Crawl prices via CSQAQ official API for all monitored items."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(WatchlistItem.market_hash_name)
            .where(WatchlistItem.enabled == True)
            .distinct()
        )
        all_items = [row[0] for row in result.all()]
        if not all_items:
            logger.info("No items to crawl")
            return
        logger.info(f"Crawling {len(all_items)} items via CSQAQ API")

        prices = await csqaq.fetch_prices(all_items)

        now = datetime.now(timezone.utc)
        snapshots = []
        for name in all_items:
            data = prices.get(name)
            if data and data.get("buff_sell"):
                snapshots.append(PriceSnapshot(
                    market_hash_name=name,
                    platform="csqaq",
                    price=data["buff_sell"],
                    timestamp=now,
                ))

        if snapshots:
            db.add_all(snapshots)
            await db.commit()
            logger.info(f"Saved {len(snapshots)} snapshots")

        # Update image URL cache
        _update_img_cache(prices)

    await run_alert_check()


async def run_alert_check():
    """Check all enabled watchlist items against latest prices."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(WatchlistItem).where(WatchlistItem.enabled == True)
        )
        items = result.scalars().all()
        alert_count = 0

        for item in items:
            price_result = await db.execute(
                select(PriceSnapshot.price, PriceSnapshot.platform)
                .where(PriceSnapshot.market_hash_name == item.market_hash_name)
                .order_by(PriceSnapshot.timestamp.desc())
                .limit(1)
            )
            latest = price_result.first()
            if not latest:
                continue
            current_price, platform = latest

            triggered = False
            message = ""

            if item.mode == 1 and check_mode_1(current_price, item.target_price):
                triggered = True
                title, content = format_price_alert(
                    item.market_hash_name, current_price, item.target_price, platform
                )
                message = f"{title}\n{content}"
            elif item.mode == 2 and check_mode_2(current_price, item.cost_price, item.threshold_pct or 5.0):
                triggered = True
                change = (current_price - item.cost_price) / item.cost_price * 100
                message = (
                    f"[CS2 持仓告警]\n{item.market_hash_name}\n"
                    f"当前: ¥{current_price:.2f} | 成本: ¥{item.cost_price:.2f} | "
                    f"{'涨幅' if change > 0 else '跌幅'}: {change:+.1f}%\n"
                    f"平台: {platform}"
                )

            if triggered:
                user_result = await db.execute(select(User).where(User.id == item.user_id))
                user = user_result.scalar_one_or_none()
                success = False
                if user and user.server_chan_key_encrypted:
                    title = f"[CS2 告警] {item.market_hash_name}"
                    success = await send_notification(user.server_chan_key_encrypted, title, message)
                    # Also send Web Push
                    await send_web_push(title, message)

                db.add(AlertLog(
                    user_id=item.user_id,
                    market_hash_name=item.market_hash_name,
                    rule_type=item.mode,
                    new_price=current_price,
                    message=message,
                    success=success,
                ))
                alert_count += 1

        await db.commit()
        logger.info(f"Alert check: {alert_count} triggered")


async def run_daily_cleanup():
    """Aggregate price data older than 30 days into hourly averages."""
    logger.info("Running daily data cleanup...")
    # TODO: Implement SQL aggregation in follow-up
    logger.info("Cleanup complete (no-op for now)")


async def run_daily_report():
    """Generate and send daily portfolio report to all users."""
    logger.info("Generating daily report...")
    # TODO: Implement per-user portfolio aggregation
    logger.info("Daily report complete (no-op for now)")
