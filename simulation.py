import math


def simulate_inventory(
    current_stock,
    daily_demand,
    sales_change_percent
):
    """
    Simulate how long current inventory will last
    when demand changes by a given percentage.
    """

    current_stock = max(float(current_stock), 0)
    daily_demand = max(float(daily_demand), 0.1)

    adjusted_demand = daily_demand * (
        1 + sales_change_percent / 100
    )

    adjusted_demand = max(
        adjusted_demand,
        0.1
    )

    days_until_stockout = math.floor(
        current_stock / adjusted_demand
    )

    remaining_stock = max(
        0,
        current_stock -
        (
            adjusted_demand *
            days_until_stockout
        )
    )

    return {
        "adjusted_demand": adjusted_demand,
        "days_until_stockout": days_until_stockout,
        "remaining_stock": remaining_stock
    }