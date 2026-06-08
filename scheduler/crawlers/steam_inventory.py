"""Steam public inventory fetcher."""
import logging
import httpx

logger = logging.getLogger(__name__)
STEAM_INVENTORY_URL = "https://steamcommunity.com/inventory/{steam_id}/730/2"


async def fetch_inventory(steam_id: str) -> list[dict]:
    url = STEAM_INVENTORY_URL.format(steam_id=steam_id)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, params={"l": "schinese", "count": 2000})
            resp.raise_for_status()
            data = resp.json()
            if not data.get("success"):
                logger.warning(f"Steam inventory private or invalid steam_id: {steam_id}")
                return []

            items = []
            descriptions = {d.get("classid"): d for d in data.get("descriptions", [])}
            for asset in data.get("assets", []):
                desc = descriptions.get(asset.get("classid"))
                if desc:
                    items.append({
                        "asset_id": asset.get("assetid", ""),
                        "market_hash_name": desc.get("market_hash_name", ""),
                        "image_url": f"https://steamcommunity-a.akamaihd.net/economy/image/{desc.get('icon_url', '')}",
                        "tradable": asset.get("tradable", False),
                    })
            return items
    except Exception as e:
        logger.error(f"Steam inventory failed: {steam_id} — {e}")
        return []
