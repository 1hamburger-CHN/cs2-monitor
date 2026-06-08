"""Notification formatting tests."""
from scheduler.notifier import format_price_alert, format_daily_report


def test_format_price_alert_shows_decline():
    title, content = format_price_alert(
        "AK-47 | Redline (Field-Tested)", 85.0, 100.0, "CSQAQ"
    )
    assert "AK-47 | Redline" in title
    assert "¥85.00" in content
    assert "跌幅" in content


def test_format_price_alert_shows_platform():
    _, content = format_price_alert(
        "AWP | Dragon Lore (Factory New)", 500.0, 450.0, "SteamDT"
    )
    assert "SteamDT" in content


def test_format_daily_report():
    items = [
        {"market_hash_name": "AK-47 | Redline", "price": 85.0, "change_pct": 2.5},
        {"market_hash_name": "AWP | Dragon Lore", "price": 500.0, "change_pct": -1.2},
    ]
    title, content = format_daily_report(items, 585.0, 0.8)
    assert "持仓日报" in title
    assert "¥585.00" in content
    assert "AK-47 | Redline" in content
