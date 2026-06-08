"""Item name mapper — loads ByMykel data and provides search/lookup."""
import json
from pathlib import Path
from typing import Optional


class ItemMapper:
    def __init__(self, data_path: str = "data/item_aliases.json"):
        self._path = Path(data_path)
        self._by_name: dict[str, dict] = {}
        self._loaded = False

    def _ensure_loaded(self):
        if self._loaded:
            return
        if not self._path.exists():
            raise FileNotFoundError(
                f"Mapping file not found: {self._path}. Run: python scripts/build_item_map.py"
            )
        with open(self._path, "r", encoding="utf-8") as f:
            self._by_name = json.load(f)
        self._loaded = True

    def get(self, market_hash_name: str) -> Optional[dict]:
        """Look up item info by exact market_hash_name."""
        self._ensure_loaded()
        return self._by_name.get(market_hash_name)

    def exists(self, market_hash_name: str) -> bool:
        """Check if market_hash_name exists in mapping."""
        self._ensure_loaded()
        return market_hash_name in self._by_name

    def search(self, query: str, limit: int = 20) -> list[dict]:
        """Fuzzy search by weapon name, skin name (supports Chinese keywords).
        Returns list of {market_hash_name, name, weapon, wear, wear_cn, rarity, ...}
        """
        self._ensure_loaded()
        query_lower = query.lower()
        results = []
        for name, info in self._by_name.items():
            if query_lower in name.lower():
                results.append({"market_hash_name": name, **info})
            elif query_lower in info.get("weapon", "").lower():
                results.append({"market_hash_name": name, **info})
            if len(results) >= limit:
                break
        return results

    @property
    def item_count(self) -> int:
        self._ensure_loaded()
        return len(self._by_name)


# Global singleton
item_mapper = ItemMapper()
