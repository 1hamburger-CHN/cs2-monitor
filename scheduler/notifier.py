"""Server酱 (Server Chan) notification sender."""
import asyncio
import logging
import httpx
from app.encryption import decrypt_value

logger = logging.getLogger(__name__)
SERVER_CHAN_URL = "https://sctapi.ftqq.com/{send_key}.send"


async def send_notification(
    send_key_encrypted: str,
    title: str,
    content: str,
    retry_count: int = 1,
    retry_delay: int = 5,
) -> bool:
    send_key = decrypt_value(send_key_encrypted)
    url = SERVER_CHAN_URL.format(send_key=send_key)

    for attempt in range(retry_count + 1):
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(url, json={"title": title, "desp": content})
                data = resp.json()
                if data.get("code") == 0:
                    logger.info(f"Notification sent: {title}")
                    return True
                else:
                    logger.warning(f"Server酱 error: {data.get('message')}")
        except Exception as e:
            logger.error(f"Notification failed (attempt {attempt+1}): {e}")

        if attempt < retry_count:
            await asyncio.sleep(retry_delay)

    logger.error(f"Notification failed after {retry_count} retries: {title}")
    return False


def format_price_alert(
    market_hash_name: str,
    current_price: float,
    target_price: float,
    platform: str,
) -> tuple[str, str]:
    """Format price alert message. Returns (title, content)."""
    change = (current_price - target_price) / target_price * 100
    title = f"[CS2 告警] {market_hash_name}"
    content = (
        f"{market_hash_name}\n\n"
        f"当前: ¥{current_price:.2f} | 目标: ¥{target_price:.2f} | "
        f"{'跌幅' if change < 0 else '价差'}: {change:+.1f}%\n"
        f"平台: {platform}"
    )
    return title, content


def format_daily_report(
    items: list[dict],
    total_value: float,
    total_change: float,
) -> tuple[str, str]:
    """Format daily report. Returns (title, content)."""
    from datetime import datetime
    date_str = datetime.now().strftime("%m月%d日")
    title = f"[CS2 持仓日报 - {date_str}]"
    lines = [f"持仓总值: ¥{total_value:,.2f} ({total_change:+.1f}%)", ""]
    for item in items:
        lines.append(
            f"{item['market_hash_name']}: ¥{item['price']:.2f} "
            f"({item['change_pct']:+.1f}%)"
        )
    return title, "\n".join(lines)
