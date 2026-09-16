import math


def calculate_reorder_recommendation(
    current_stock,
    daily_demand,
    lead_time_days,
    minimum_stock,
    safety_days=3
):
    """
    Calculate inventory reorder recommendation.

    Parameters:
        current_stock: Current available stock
        daily_demand: Estimated average daily demand
        lead_time_days: Supplier lead time
        minimum_stock: Minimum required stock level
        safety_days: Additional safety-stock coverage

    Returns:
        Dictionary containing reorder point,
        recommended quantity and decision.
    """

    current_stock = max(float(current_stock), 0)
    daily_demand = max(float(daily_demand), 0)
    lead_time_days = max(int(lead_time_days), 0)
    minimum_stock = max(float(minimum_stock), 0)
    safety_days = max(int(safety_days), 0)

    # Stock needed during supplier lead time
    lead_time_demand = (
        daily_demand * lead_time_days
    )

    # Additional safety stock
    safety_stock = (
        daily_demand * safety_days
    )

    # Reorder point
    reorder_point = (
        lead_time_demand
        + safety_stock
        + minimum_stock
    )

    # Recommended order quantity
    if current_stock < reorder_point:

        recommended_quantity = math.ceil(
            reorder_point - current_stock
        )

        decision = "REORDER NOW"

    else:

        recommended_quantity = 0

        decision = "STOCK SUFFICIENT"

    return {
        "lead_time_demand": lead_time_demand,
        "safety_stock": safety_stock,
        "reorder_point": reorder_point,
        "recommended_quantity": recommended_quantity,
        "decision": decision
    }