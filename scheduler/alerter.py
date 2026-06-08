"""Alert rule engine — pure functions, no side effects."""


def check_mode_1(current_price: float, target_price: float | None) -> bool:
    """Mode 1 — Single item target price: current <= target -> alert."""
    if target_price is None:
        return False
    return current_price <= target_price


def check_mode_2(
    current_price: float,
    cost_price: float | None,
    threshold_pct: float = 5.0,
) -> bool:
    """Mode 2 — Portfolio: |current - cost| / cost >= threshold% -> alert."""
    if cost_price is None or cost_price <= 0:
        return False
    change_pct = abs(current_price - cost_price) / cost_price * 100
    return change_pct >= threshold_pct


def check_mode_3(
    price_changes: dict[str, float],
    top_n: int = 5,
) -> dict[str, list[tuple[str, float]]]:
    """Mode 3 — Market scan: Top N gainers and losers."""
    sorted_items = sorted(price_changes.items(), key=lambda x: x[1], reverse=True)
    return {
        "top_gainers": sorted_items[:top_n],
        "top_losers": sorted_items[-top_n:],
    }
