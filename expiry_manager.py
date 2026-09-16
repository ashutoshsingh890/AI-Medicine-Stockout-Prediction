from datetime import date
import sqlite3
from pathlib import Path
import pandas as pd

BASE = Path(__file__).parent
DB_FILE = BASE / "medicine_inventory.db"


def get_connection():
    return sqlite3.connect(DB_FILE)


def get_expiry_risk():
    """
    Calculate expiry risk for all medicines.
    """

    conn = get_connection()

    rows = conn.execute("""
        SELECT
            id,
            name,
            category,
            supplier,
            expiry_date,
            batch_number
        FROM medicines
        ORDER BY name
    """).fetchall()

    conn.close()

    columns = [
        "id",
        "name",
        "category",
        "supplier",
        "expiry_date",
        "batch_number"
    ]

    df = pd.DataFrame(rows, columns=columns)

    if df.empty:
        return df

    today = date.today()

    def calculate_days(expiry):
        if not expiry:
            return None

        try:
            expiry_dt = date.fromisoformat(str(expiry))
            return (expiry_dt - today).days
        except ValueError:
            return None

    df["days_remaining"] = df["expiry_date"].apply(
        calculate_days
    )

    def get_risk(days):
        if days is None:
            return "No Expiry Date"
        elif days < 0:
            return "Expired"
        elif days <= 30:
            return "Critical"
        elif days <= 90:
            return "Warning"
        else:
            return "Safe"

    df["risk_status"] = df["days_remaining"].apply(
        get_risk
    )

    return df


def get_expiry_summary():
    """
    Return expiry risk counts.
    """

    df = get_expiry_risk()

    if df.empty:
        return {
            "expired": 0,
            "critical": 0,
            "warning": 0,
            "safe": 0,
            "no_expiry": 0
        }

    return {
        "expired": int(
            (df["risk_status"] == "Expired").sum()
        ),
        "critical": int(
            (df["risk_status"] == "Critical").sum()
        ),
        "warning": int(
            (df["risk_status"] == "Warning").sum()
        ),
        "safe": int(
            (df["risk_status"] == "Safe").sum()
        ),
        "no_expiry": int(
            (df["risk_status"] == "No Expiry Date").sum()
        )
    }