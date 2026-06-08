#!/usr/bin/env python3
"""Fetch CS2 skin data from ByMykel/CSGO-API and build local mapping table.
Usage: python scripts/build_item_map.py
Output: data/item_aliases.json
"""
import json
import httpx

API_URL = "https://raw.githubusercontent.com/ByMykel/CSGO-API/main/public/api/en/skins.json"
WEAR_CN = {
    "Factory New": "崭新出厂",
    "Minimal Wear": "略有磨损",
    "Field-Tested": "久经沙场",
    "Well-Worn": "破损不堪",
    "Battle-Scarred": "战痕累累",
}


def build_market_hash_name(name: str, wear: str, stattrak: bool = False, souvenir: bool = False) -> str:
    prefix = "Souvenir " if souvenir else ("StatTrak™ " if stattrak else "")
    return f"{prefix}{name} ({wear})"


def main():
    print("Fetching skins from ByMykel/CSGO-API...")
    resp = httpx.get(API_URL, timeout=60)
    resp.raise_for_status()
    skins = resp.json()

    aliases = {}
    for skin in skins:
        name = skin["name"]
        wears = skin.get("wears", [])
        stattrak = skin.get("stattrak", False)
        souvenir = skin.get("souvenir", False)
        weapon_name = skin.get("weapon", {}).get("name", "")
        rarity = skin.get("rarity", {}).get("name", "")

        for wear in wears:
            wear_name = wear["name"]

            # Non-StatTrak version
            mn = build_market_hash_name(name, wear_name)
            aliases[mn] = {
                "name": name,
                "weapon": weapon_name,
                "wear": wear_name,
                "wear_cn": WEAR_CN.get(wear_name, wear_name),
                "rarity": rarity,
                "stattrak": False,
                "souvenir": souvenir,
            }

            # StatTrak version (if skin has StatTrak variant)
            if stattrak:
                st_name = build_market_hash_name(name, wear_name, stattrak=True)
                aliases[st_name] = {
                    "name": name,
                    "weapon": weapon_name,
                    "wear": wear_name,
                    "wear_cn": WEAR_CN.get(wear_name, wear_name),
                    "rarity": rarity,
                    "stattrak": True,
                    "souvenir": False,
                }

    with open("data/item_aliases.json", "w", encoding="utf-8") as f:
        json.dump(aliases, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(aliases)} entries -> data/item_aliases.json")


if __name__ == "__main__":
    main()
