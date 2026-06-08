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


def _load_cache():
    global _id_cache
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r") as f:
            _id_cache = json.load(f)


def _save_cache():
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(_id_cache, f)


_load_cache()


async def _search_suggest(client: httpx.AsyncClient, text: str) -> list[dict]:
    try:
        resp = await client.get(
            f"{CSQAQ_BASE}/api/v1/search/suggest",
            params={"text": text},
            headers={"ApiToken": CSQAQ_TOKEN},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("data", [])
    except Exception as e:
        logger.error(f"CSQAQ suggest error: {e}")
    return []


async def _get_detail(client: httpx.AsyncClient, csqaq_id: int) -> Optional[dict]:
    try:
        resp = await client.get(
            f"{CSQAQ_BASE}/api/v1/info/good",
            params={"id": csqaq_id},
            headers={"ApiToken": CSQAQ_TOKEN},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("data", {}).get("goods_info")
    except Exception as e:
        logger.error(f"CSQAQ detail error id={csqaq_id}: {e}")
    return None


async def resolve_id(client: httpx.AsyncClient, market_hash_name: str) -> Optional[int]:
    if market_hash_name in _id_cache:
        return _id_cache[market_hash_name]

    weapon = market_hash_name.split(" | ")[0] if " | " in market_hash_name else market_hash_name
    suggestions = await _search_suggest(client, weapon)
    if not suggestions:
        return None

    for s in suggestions[:30]:
        cid = int(s["id"])
        detail = await _get_detail(client, cid)
        if detail and detail.get("market_hash_name") == market_hash_name:
            _id_cache[market_hash_name] = cid
            _save_cache()
            return cid

    return None


async def fetch_price(
    market_hash_name: str,
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
) -> Optional[dict]:
    async with semaphore:
        try:
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
            }
        except Exception as e:
            logger.error(f"CSQAQ error {market_hash_name}: {e}")
            return None


async def fetch_prices(
    items: list[str],
    timeout: int = 10,
    max_concurrent: int = 3,
) -> dict[str, Optional[dict]]:
    semaphore = asyncio.Semaphore(max_concurrent)
    async with httpx.AsyncClient(timeout=timeout) as client:
        tasks = {name: fetch_price(name, client, semaphore) for name in items}
        results = {}
        for name, task in tasks.items():
            results[name] = await task
    return results
