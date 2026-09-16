import sqlite3
from pathlib import Path
import pandas as pd

BASE = Path(__file__).parent
DB_FILE = BASE / "medicine_inventory.db"


def get_connection():
    return sqlite3.connect(DB_FILE)


def init_inventory_database():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS inventory_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicine_id INTEGER NOT NULL,
            transaction_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            transaction_date TEXT NOT NULL,
            batch_number TEXT DEFAULT '',
            notes TEXT DEFAULT ''
        )
    """)

    conn.commit()
    conn.close()


def add_transaction(
    medicine_id,
    transaction_type,
    quantity,
    transaction_date,
    batch_number="",
    notes=""
):
    init_inventory_database()

    conn = get_connection()

    try:
        conn.execute("""
            INSERT INTO inventory_transactions
            (
                medicine_id,
                transaction_type,
                quantity,
                transaction_date,
                batch_number,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            int(medicine_id),
            transaction_type,
            int(quantity),
            transaction_date,
            batch_number.strip(),
            notes.strip()
        ))

        conn.commit()

        return True, "Transaction added successfully."

    except Exception as e:
        return False, f"Error: {e}"

    finally:
        conn.close()


def get_transactions():
    init_inventory_database()

    conn = get_connection()

    rows = conn.execute("""
        SELECT
            t.id,
            t.medicine_id,
            m.name AS medicine,
            t.transaction_type,
            t.quantity,
            t.transaction_date,
            t.batch_number,
            t.notes
        FROM inventory_transactions t
        LEFT JOIN medicines m
            ON t.medicine_id = m.id
        ORDER BY t.id DESC
    """).fetchall()

    conn.close()

    columns = [
        "id",
        "medicine_id",
        "medicine",
        "transaction_type",
        "quantity",
        "transaction_date",
        "batch_number",
        "notes"
    ]

    return pd.DataFrame(rows, columns=columns)


def get_current_stock(medicine_id):
    init_inventory_database()

    conn = get_connection()

    row = conn.execute("""
        SELECT
            COALESCE(
                SUM(
                    CASE
                        WHEN transaction_type = 'STOCK_IN'
                        THEN quantity
                        WHEN transaction_type = 'SALE'
                        THEN -quantity
                        ELSE 0
                    END
                ),
                0
            )
        FROM inventory_transactions
        WHERE medicine_id = ?
    """, (int(medicine_id),)).fetchone()

    conn.close()

    return int(row[0])


def get_stock_summary():
    init_inventory_database()

    conn = get_connection()

    rows = conn.execute("""
        SELECT
            m.id,
            m.name,
            m.category,
            m.unit,
            m.minimum_stock,
            COALESCE(
                SUM(
                    CASE
                        WHEN t.transaction_type = 'STOCK_IN'
                        THEN t.quantity
                        WHEN t.transaction_type = 'SALE'
                        THEN -t.quantity
                        ELSE 0
                    END
                ),
                0
            ) AS current_stock
        FROM medicines m
        LEFT JOIN inventory_transactions t
            ON m.id = t.medicine_id
        GROUP BY
            m.id,
            m.name,
            m.category,
            m.unit,
            m.minimum_stock
        ORDER BY m.name
    """).fetchall()

    conn.close()

    columns = [
        "id",
        "name",
        "category",
        "unit",
        "minimum_stock",
        "current_stock"
    ]

    return pd.DataFrame(rows, columns=columns)