"""Item mapper tests."""
import pytest
from app.item_mapper import ItemMapper


@pytest.fixture
def mapper():
    """Create mapper with test data, bypassing file loading."""
    m = ItemMapper.__new__(ItemMapper)
    m._path = None
    m._loaded = True
    m._by_name = {
        "AK-47 | Redline (Field-Tested)": {
            "name": "AK-47 | Redline",
            "weapon": "AK-47",
            "wear": "Field-Tested",
            "wear_cn": "久经沙场",
            "rarity": "Classified",
            "stattrak": False,
            "souvenir": False,
        },
        "AWP | Dragon Lore (Factory New)": {
            "name": "AWP | Dragon Lore",
            "weapon": "AWP",
            "wear": "Factory New",
            "wear_cn": "崭新出厂",
            "rarity": "Covert",
            "stattrak": False,
            "souvenir": False,
        },
        "StatTrak™ AK-47 | Redline (Field-Tested)": {
            "name": "AK-47 | Redline",
            "weapon": "AK-47",
            "wear": "Field-Tested",
            "wear_cn": "久经沙场",
            "rarity": "Classified",
            "stattrak": True,
            "souvenir": False,
        },
    }
    return m


def test_exists_returns_true_for_known_item(mapper):
    assert mapper.exists("AK-47 | Redline (Field-Tested)") is True


def test_exists_returns_false_for_unknown_item(mapper):
    assert mapper.exists("Fake Gun (Factory New)") is False


def test_search_by_weapon_name(mapper):
    results = mapper.search("AWP")
    assert len(results) == 1
    assert results[0]["market_hash_name"] == "AWP | Dragon Lore (Factory New)"


def test_search_case_insensitive(mapper):
    results = mapper.search("redline")
    assert len(results) >= 1


def test_get_returns_item_info(mapper):
    info = mapper.get("AK-47 | Redline (Field-Tested)")
    assert info is not None
    assert info["rarity"] == "Classified"
    assert info["wear_cn"] == "久经沙场"


def test_get_stattrak_variant(mapper):
    info = mapper.get("StatTrak™ AK-47 | Redline (Field-Tested)")
    assert info is not None
    assert info["stattrak"] is True


def test_search_returns_empty_for_no_match(mapper):
    results = mapper.search("zzz_nonexistent_zzz")
    assert len(results) == 0
