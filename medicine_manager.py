import sqlite3
from pathlib import Path
import pandas as pd

BASE = Path(__file__).parent
DB_FILE = BASE / "medicine_inventory.db"
DATA_FILE = BASE / "data/medicine_sales.csv"


def get_connection():
    return sqlite3.connect(DB_FILE)


def init_database():

    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            category TEXT,
            unit TEXT DEFAULT 'units',
            minimum_stock INTEGER DEFAULT 100,
            supplier TEXT DEFAULT '',
            lead_time_days INTEGER DEFAULT 7,
            expiry_date TEXT DEFAULT '',
            batch_number TEXT DEFAULT ''
        )
    """)

    # Existing database ke liye missing columns safely add karna
    columns = [
        row[1]
        for row in conn.execute(
            "PRAGMA table_info(medicines)"
        ).fetchall()
    ]

    if "expiry_date" not in columns:
        conn.execute(
            "ALTER TABLE medicines ADD COLUMN expiry_date TEXT DEFAULT ''"
        )

    if "batch_number" not in columns:
        conn.execute(
            "ALTER TABLE medicines ADD COLUMN batch_number TEXT DEFAULT ''"
        )

    conn.commit()
    conn.close()


def seed_medicines():

    init_database()

    conn = get_connection()

    try:

        df = pd.read_csv(DATA_FILE)

        if "medicine_name" not in df.columns:
            return

        medicines = df["medicine_name"].dropna().unique()

        for medicine in medicines:

            medicine = str(medicine).strip()

            if medicine:

                conn.execute("""
                    INSERT OR IGNORE INTO medicines
                    (
                        name,
                        category,
                        unit,
                        minimum_stock,
                        supplier,
                        lead_time_days,
                        expiry_date,
                        batch_number
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    medicine,
                    "General",
                    "units",
                    100,
                    "Default Supplier",
                    7,
                    "",
                    ""
                ))

        conn.commit()

    finally:
        conn.close()


def get_medicines():

    init_database()

    conn = get_connection()

    rows = conn.execute("""
        SELECT
            id,
            name,
            category,
            unit,
            minimum_stock,
            supplier,
            lead_time_days,
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
        "unit",
        "minimum_stock",
        "supplier",
        "lead_time_days",
        "expiry_date",
        "batch_number"
    ]

    return pd.DataFrame(
        rows,
        columns=columns
    )


def add_medicine(
    name,
    category,
    unit,
    minimum_stock,
    supplier,
    lead_time_days,
    expiry_date="",
    batch_number=""
):

    init_database()

    conn = get_connection()

    try:

        conn.execute("""
            INSERT INTO medicines
            (
                name,
                category,
                unit,
                minimum_stock,
                supplier,
                lead_time_days,
                expiry_date,
                batch_number
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name.strip(),
            category.strip(),
            unit.strip(),
            int(minimum_stock),
            supplier.strip(),
            int(lead_time_days),
            str(expiry_date),
            batch_number.strip()
        ))

        conn.commit()

        return True, "Medicine added successfully."

    except sqlite3.IntegrityError:

        return False, "Medicine already exists."

    except Exception as e:

        return False, f"Error: {e}"

    finally:
        conn.close()


def update_medicine(
    medicine_id,
    name,
    category,
    unit,
    minimum_stock,
    supplier,
    lead_time_days,
    expiry_date="",
    batch_number=""
):

    init_database()

    conn = get_connection()

    try:

        conn.execute("""
            UPDATE medicines
            SET
                name = ?,
                category = ?,
                unit = ?,
                minimum_stock = ?,
                supplier = ?,
                lead_time_days = ?,
                expiry_date = ?,
                batch_number = ?
            WHERE id = ?
        """, (
            name.strip(),
            category.strip(),
            unit.strip(),
            int(minimum_stock),
            supplier.strip(),
            int(lead_time_days),
            str(expiry_date),
            batch_number.strip(),
            int(medicine_id)
        ))

        conn.commit()

        return True, "Medicine updated successfully."

    except sqlite3.IntegrityError:

        return False, "Another medicine already has this name."

    except Exception as e:

        return False, f"Error: {e}"

    finally:
        conn.close()


def delete_medicine(medicine_id):

    init_database()

    conn = get_connection()

    conn.execute(
        "DELETE FROM medicines WHERE id = ?",
        (int(medicine_id),)
    )

    conn.commit()
    conn.close()


def get_supplier_names():

    init_supplier_connection = get_connection()

    try:

        rows = init_supplier_connection.execute("""
            SELECT name
            FROM suppliers
            ORDER BY name
        """).fetchall()

        return [row[0] for row in rows]

    except sqlite3.OperationalError:

        return []

    finally:

        init_supplier_connection.close()