import sqlite3
from pathlib import Path
import pandas as pd

BASE = Path(__file__).parent
DB_FILE = BASE / "medicine_inventory.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():
    return sqlite3.connect(DB_FILE)


# =========================================================
# INITIALIZE SUPPLIER TABLE
# =========================================================

def init_supplier_database():

    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            contact_person TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            email TEXT DEFAULT '',
            address TEXT DEFAULT '',
            reliability REAL DEFAULT 90,
            average_lead_time INTEGER DEFAULT 7
        )
    """)

    conn.commit()
    conn.close()


# =========================================================
# GET SUPPLIERS
# =========================================================

def get_suppliers():

    init_supplier_database()

    conn = get_connection()

    rows = conn.execute("""
        SELECT
            id,
            name,
            contact_person,
            phone,
            email,
            address,
            reliability,
            average_lead_time
        FROM suppliers
        ORDER BY name
    """).fetchall()

    conn.close()

    columns = [
        "id",
        "name",
        "contact_person",
        "phone",
        "email",
        "address",
        "reliability",
        "average_lead_time"
    ]

    return pd.DataFrame(
        rows,
        columns=columns
    )


# =========================================================
# ADD SUPPLIER
# =========================================================

def add_supplier(
    name,
    contact_person,
    phone,
    email,
    address,
    reliability,
    average_lead_time
):

    init_supplier_database()

    conn = get_connection()

    try:

        conn.execute("""
            INSERT INTO suppliers
            (
                name,
                contact_person,
                phone,
                email,
                address,
                reliability,
                average_lead_time
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            name.strip(),
            contact_person.strip(),
            phone.strip(),
            email.strip(),
            address.strip(),
            float(reliability),
            int(average_lead_time)
        ))

        conn.commit()

        return True, "Supplier added successfully."

    except sqlite3.IntegrityError:

        return False, "Supplier already exists."

    except Exception as e:

        return False, f"Error: {e}"

    finally:

        conn.close()


# =========================================================
# UPDATE SUPPLIER
# =========================================================

def update_supplier(
    supplier_id,
    name,
    contact_person,
    phone,
    email,
    address,
    reliability,
    average_lead_time
):

    init_supplier_database()

    conn = get_connection()

    try:

        conn.execute("""
            UPDATE suppliers
            SET
                name = ?,
                contact_person = ?,
                phone = ?,
                email = ?,
                address = ?,
                reliability = ?,
                average_lead_time = ?
            WHERE id = ?
        """, (
            name.strip(),
            contact_person.strip(),
            phone.strip(),
            email.strip(),
            address.strip(),
            float(reliability),
            int(average_lead_time),
            int(supplier_id)
        ))

        conn.commit()

        return True, "Supplier updated successfully."

    except sqlite3.IntegrityError:

        return False, "Another supplier already has this name."

    except Exception as e:

        return False, f"Error: {e}"

    finally:

        conn.close()


# =========================================================
# DELETE SUPPLIER
# =========================================================

def delete_supplier(supplier_id):

    init_supplier_database()

    conn = get_connection()

    conn.execute(
        "DELETE FROM suppliers WHERE id = ?",
        (int(supplier_id),)
    )

    conn.commit()
    conn.close()