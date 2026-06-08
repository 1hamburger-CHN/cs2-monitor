"""CSQAQ price crawler — async httpx with semaphore."""
import asyncio
import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)
CSQAQ_SEARCH_URL = "https://www.csgoaq.com/api/search"


async def fetch_price(
    market_hash_name: str,
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
) -> Optional[float]:
    async with semaphore:
        try:
            resp = await client.get(
                CSQAQ_SEARCH_URL,
                params={"keyword": market_hash_name},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("data", [])
            if items:
                price = items[0].get("price") or items[0].get("min_price")
                return float(price) if price else None
            return None
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning(f"CSQAQ 429, waiting 60s...")
                await asyncio.sleep(60)
            return None
        except httpx.TimeoutException:
            logger.warning(f"CSQAQ timeout: {market_hash_name}")
            return None
        except Exception as e:
            logger.error(f"CSQAQ error: {market_hash_name} — {e}")
            return None


async def fetch_prices(
    items: list[str],
    timeout: int = 15,
    max_concurrent: int = 5,
) -> dict[str, Optional[float]]:
    semaphore = asyncio.Semaphore(max_concurrent)
    async with httpx.AsyncClient(timeout=timeout) as client:
        tasks = {name: fetch_price(name, client, semaphore) for name in items}
        results = {}
        for name, task in tasks.items():
            results[name] = await task
    return results
