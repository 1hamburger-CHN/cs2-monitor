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

        # Load Chinese names from CSQAQ ID file
        self._cn_names: dict[str, str] = {}
        csqaq_file = Path("data/csqaq_ids.json")
        if csqaq_file.exists():
            data = json.loads(csqaq_file.read_text(encoding="utf-8"))
            for item in data:
                cn = item.get("name", "")
                en = item.get("market_hash_name", "")
                if cn and en and en in self._by_name:
                    self._cn_names[cn] = en
        # Build reverse index: English name -> Chinese name
        self._en_to_cn: dict[str, str] = {}
        for cn_name, en_name in self._cn_names.items():
            if en_name not in self._en_to_cn:
                self._en_to_cn[en_name] = cn_name
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
        self._ensure_loaded()
        query_lower = query.lower()
        matched: dict[str, int] = {}

        # 1. Chinese full-name match (from CSQAQ ID file)
        for cn_name, en_name in self._cn_names.items():
            if query in cn_name:
                matched[en_name] = max(matched.get(en_name, 0), 90)

        # 2. English name substring match
        for name, info in self._by_name.items():
            score = 0
            if query_lower in name.lower():
                score = 100
            elif query_lower in info.get('weapon', '').lower():
                score = 50
            elif info.get('wear_cn', '') and query_lower in info['wear_cn']:
                score = 20
            if score > 0:
                matched[name] = max(matched.get(name, 0), score)

        # 3. Multi-keyword matching
        tokens = query_lower.replace('|', ' ').replace('-', ' ').split()
        if len(tokens) > 1:
            for name, info in self._by_name.items():
                hits = 0
                search_text = f"{info.get('weapon', '')} {info.get('wear_cn', '')}".lower()
                for token in tokens:
                    if token in search_text:
                        hits += 1
                if hits >= len(tokens) * 0.5:
                    matched[name] = max(matched.get(name, 0), hits * 3)

        sorted_results = sorted(matched.items(), key=lambda x: x[1], reverse=True)
        results = []
        for name, _ in sorted_results[:limit]:
            item = {"market_hash_name": name, **self._by_name[name]}
            item["cn_name"] = self._en_to_cn.get(name, name)
            results.append(item)
        return results

    @property
    def item_count(self) -> int:
        self._ensure_loaded()
        return len(self._by_name)


# Global singleton
item_mapper = ItemMapper()
