"""SteamDT price crawler — async httpx with semaphore."""
import asyncio
import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)
STEAMDT_API = "https://www.steamdt.com/api/price"


async def fetch_price(
    market_hash_name: str,
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
) -> Optional[float]:
    async with semaphore:
        try:
            resp = await client.get(
                STEAMDT_API,
                params={"name": market_hash_name},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            price = data.get("price") or data.get("current_price")
            return float(price) if price else None
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning(f"SteamDT 429, waiting 60s...")
                await asyncio.sleep(60)
            return None
        except httpx.TimeoutException:
            logger.warning(f"SteamDT timeout: {market_hash_name}")
            return None
        except Exception as e:
            logger.error(f"SteamDT error: {market_hash_name} — {e}")
            return None


async def fetch_prices(
    items: list[str],
    timeout: int = 15,
    max_concurrent: int = 5,
) -> dict[str, Optional[float]]:
    semaphore = asyncio.Semaphore(max_concurrent)
    async with httpx.AsyncClient(timeout=timeout) as client:
        tasks = {name: fetch_price(name, client, semaphore) for name in items}
        return {name: await task for name, task in tasks.items()}
