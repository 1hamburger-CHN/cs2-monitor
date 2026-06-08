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
        # Build Chinese search index
        self._cn_index: dict[str, set[str]] = {}
        # Common Chinese skin name keywords (partial matches supported)
        CN_SKIN_KEYWORDS = {
            "红线": "redline", "二西莫夫": "asiimov", "龙狙": "dragon lore",
            "火神": "vulcan", "咆哮": "howl", "皇后": "empress",
            "水栽竹": "aquamarine", "大马士革": "damascus", "多普勒": "doppler",
            "渐变": "fade", "深红": "crimson", "屠夫": "slaughter",
            "森林": "forest", "沙漠": "sand", "城市": "urban",
            "血腥": "blood", "狩猎": "safari", "卫星": "moon",
            "蓝钢": "blue steel", "淬火": "case hardened", "蛇": "safari mesh",
            "钛": "titanium", "大理石": "marble", "虎牙": "tiger tooth",
            "自动化": "autotronic", "传说": "lore", "自由": "freedom",
            "暴怒": "fury", "狂": "rage", "魅影": "phantom",
            "复仇": "vengeance", "恶魔": "demon", "天使": "angel",
            "蛇纹": "snake", "黑": "black", "白": "white", "金": "gold",
            "赤": "red", "蓝图": "blueprint", "机械": "mechanical",
        }
        for mn, info in self._by_name.items():
            keywords = set()
            weapon = info.get("weapon", "")
            skin_name = info.get("name", "").lower()
            wear_cn = info.get("wear_cn", "")
            for token in weapon.lower().replace("-", " ").split():
                keywords.add(token)
            if wear_cn:
                keywords.add(wear_cn)
                for i in range(1, len(wear_cn)):
                    keywords.add(wear_cn[:i + 1])
            # Match Chinese keywords against English skin name
            for cn_kw, en_kw in CN_SKIN_KEYWORDS.items():
                if en_kw in skin_name and cn_kw not in keywords:
                    keywords.add(cn_kw)
                    for i in range(1, len(cn_kw)):
                        keywords.add(cn_kw[:i + 1])
            for kw in keywords:
                self._cn_index.setdefault(kw, set()).add(mn)
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
        """Fuzzy search by weapon name, skin name, Chinese keywords.
        Returns list of {market_hash_name, name, weapon, wear, wear_cn, rarity, ...}
        """
        self._ensure_loaded()
        query_lower = query.lower()
        matched: dict[str, int] = {}  # market_hash_name -> score

        # 1. English name exact substring match (highest priority)
        for name, info in self._by_name.items():
            score = 0
            if query_lower in name.lower():
                score = 100
            elif query_lower in info.get("weapon", "").lower():
                score = 50
            if score > 0:
                matched[name] = score

        # 2. Chinese keyword match (character-level) — skip in mock/test mode
        if hasattr(self, '_cn_index'):
            for kw, names in self._cn_index.items():
                if kw in query_lower:
                    for name in names:
                        matched[name] = matched.get(name, 0) + 1

        # 3. Tokenized multi-keyword matching
        tokens = query_lower.replace("|", " ").replace("-", " ").split()
        if len(tokens) > 1:
            for name, info in self._by_name.items():
                hits = 0
                search_text = f"{info.get('weapon', '')} {info.get('wear_cn', '')}".lower()
                for token in tokens:
                    if token in search_text:
                        hits += 1
                if hits >= len(tokens) * 0.5:  # At least half the tokens match
                    matched[name] = matched.get(name, 0) + hits * 3

        # Sort by score, return top results
        sorted_results = sorted(matched.items(), key=lambda x: x[1], reverse=True)
        results = []
        for name, _ in sorted_results[:limit]:
            results.append({"market_hash_name": name, **self._by_name[name]})
        return results

    @property
    def item_count(self) -> int:
        self._ensure_loaded()
        return len(self._by_name)


# Global singleton
item_mapper = ItemMapper()
