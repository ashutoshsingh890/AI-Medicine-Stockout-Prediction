from datetime import date
import pandas as pd


def get_inventory_alerts(medicines_df, stock_df):
    """
    Generate inventory and expiry alerts.
    """

    alerts = []

    if medicines_df.empty:
        return pd.DataFrame(
            columns=[
                "medicine",
                "alert_type",
                "message",
                "priority"
            ]
        )

    for _, medicine in medicines_df.iterrows():

        medicine_id = int(medicine["id"])
        medicine_name = medicine["name"]

        minimum_stock = float(
            medicine["minimum_stock"]
        )

        # -----------------------------------------
        # CURRENT STOCK
        # -----------------------------------------

        stock_row = stock_df[
            stock_df["id"] == medicine_id
        ]

        if stock_row.empty:
            current_stock = 0
        else:
            current_stock = int(
                stock_row["current_stock"].iloc[0]
            )

        # -----------------------------------------
        # STOCK ALERTS
        # -----------------------------------------

        if current_stock <= 0:

            alerts.append({
                "medicine": medicine_name,
                "alert_type": "OUT OF STOCK",
                "message": "Medicine is currently out of stock.",
                "priority": "HIGH"
            })

        elif current_stock < minimum_stock:

            alerts.append({
                "medicine": medicine_name,
                "alert_type": "LOW STOCK",
                "message": (
                    f"Current stock is {current_stock} units "
                    f"which is below minimum stock of "
                    f"{minimum_stock:.0f} units."
                ),
                "priority": "MEDIUM"
            })

        # -----------------------------------------
        # EXPIRY ALERTS
        # -----------------------------------------

        expiry_value = medicine.get(
            "expiry_date",
            ""
        )

        if (
            expiry_value is not None
            and str(expiry_value).strip() != ""
        ):

            try:

                expiry_date = pd.to_datetime(
                    expiry_value
                ).date()

                today = date.today()

                days_left = (
                    expiry_date - today
                ).days

                if days_left < 0:

                    alerts.append({
                        "medicine": medicine_name,
                        "alert_type": "EXPIRED",
                        "message": (
                            f"Medicine expired "
                            f"{abs(days_left)} days ago."
                        ),
                        "priority": "HIGH"
                    })

                elif days_left <= 30:

                    alerts.append({
                        "medicine": medicine_name,
                        "alert_type": "EXPIRING SOON",
                        "message": (
                            f"Medicine will expire in "
                            f"{days_left} days."
                        ),
                        "priority": "MEDIUM"
                    })

            except Exception:
                pass

    return pd.DataFrame(alerts)