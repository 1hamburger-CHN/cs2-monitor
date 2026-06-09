"""CSQAQ official API crawler — https://docs.csqaq.com"""
import asyncio
import json
import logging
import os
from pathlib import Path
import httpx
from typing import Optional

logger = logging.getLogger(__name__)

CSQAQ_BASE = "https://api.csqaq.com"
CSQAQ_TOKEN = os.environ.get("CSQAQ_API_TOKEN", "")
CACHE_FILE = Path("data/csqaq_id_cache.json")

_id_cache: dict[str, int] = {}
_id_lookup: dict[str, int] = {}  # market_hash_name -> CSQAQ ID

ID_LOOKUP_FILE = Path("data/csqaq_ids.json")


def _load_lookup():
    """Load the full CSQAQ ID mapping file (market_hash_name -> id)."""
    global _id_lookup
    if ID_LOOKUP_FILE.exists():
        try:
            data = json.loads(ID_LOOKUP_FILE.read_text(encoding="utf-8"))
            for item in data:
                name = item.get("market_hash_name", "")
                if name:
                    _id_lookup[name] = int(item["id"])
            logger.info(f"Loaded {len(_id_lookup)} CSQAQ IDs from lookup file")
        except Exception as e:
            logger.warning(f"Failed to load ID lookup: {e}")


def _load_cache():
    global _id_cache
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r") as f:
            _id_cache = json.load(f)


def _save_cache():
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(_id_cache, f)


_load_lookup()
_load_cache()


async def _request(client: httpx.AsyncClient, url: str, params: dict) -> Optional[dict]:
    """Make API request with 429 retry."""
    for attempt in range(3):
        try:
            resp = await client.get(
                url, params=params,
                headers={"ApiToken": CSQAQ_TOKEN},
                timeout=10,
            )
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 429:
                wait = 2 * (attempt + 1)
                logger.warning(f"CSQAQ 429, waiting {wait}s...")
                await asyncio.sleep(wait)
                continue
            logger.warning(f"CSQAQ HTTP {resp.status_code}")
            return None
        except Exception as e:
            logger.error(f"CSQAQ request error: {e}")
            await asyncio.sleep(1)
    return None


async def _search_suggest(client: httpx.AsyncClient, text: str) -> list[dict]:
    data = await _request(client, f"{CSQAQ_BASE}/api/v1/search/suggest", {"text": text})
    return data.get("data", []) if data else []


async def _get_detail(client: httpx.AsyncClient, csqaq_id: int) -> Optional[dict]:
    data = await _request(client, f"{CSQAQ_BASE}/api/v1/info/good", {"id": csqaq_id})
    return data.get("data", {}).get("goods_info") if data else None


async def resolve_id(client: httpx.AsyncClient, market_hash_name: str) -> Optional[int]:
    """Resolve CSQAQ ID for a market_hash_name. Cached after first lookup."""
    if market_hash_name in _id_cache:
        return _id_cache[market_hash_name]

    # Try full ID lookup first (fast path)
    if market_hash_name in _id_lookup:
        cid = _id_lookup[market_hash_name]
        _id_cache[market_hash_name] = cid
        return cid

    # Fall back to search API (slow path)
    weapon = market_hash_name.split(" | ")[0] if " | " in market_hash_name else market_hash_name

    from app.item_mapper import item_mapper
    info = item_mapper.get(market_hash_name)
    wear_cn = info.get("wear_cn", "") if info else ""

    queries = []
    if wear_cn:
        queries.append(f"{weapon} {wear_cn}")
    queries.append(weapon)

    for query in queries:
        suggestions = await _search_suggest(client, query)
        if not suggestions:
            continue
        for s in suggestions:
            cid = int(s["id"])
            detail = await _get_detail(client, cid)
            if detail and detail.get("market_hash_name") == market_hash_name:
                _id_cache[market_hash_name] = cid
                _save_cache()
                return cid
            await asyncio.sleep(0.3)

    return None


async def fetch_price(
    market_hash_name: str,
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
) -> Optional[dict]:
    async with semaphore:
        cid = await resolve_id(client, market_hash_name)
        if cid is None:
            return None
        detail = await _get_detail(client, cid)
        if detail is None:
            return None
        return {
            "buff_sell": detail.get("buff_sell_price"),
            "buff_buy": detail.get("buff_buy_price"),
            "yyyp_sell": detail.get("yyyp_sell_price"),
            "c5_sell": detail.get("c5_sell_price"),
            "steam_sell": detail.get("steam_sell_price"),
            "img_url": detail.get("img"),
        }


async def fetch_prices(
    items: list[str],
    timeout: int = 10,
    max_concurrent: int = 1,  # Single request at a time to avoid 429
) -> dict[str, Optional[dict]]:
    semaphore = asyncio.Semaphore(max_concurrent)
    async with httpx.AsyncClient(timeout=timeout) as client:
        tasks = {name: fetch_price(name, client, semaphore) for name in items}
        results = {}
        for name, task in tasks.items():
            results[name] = await task
    return results
