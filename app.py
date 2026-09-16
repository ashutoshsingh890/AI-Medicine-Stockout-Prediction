import json
from pathlib import Path
from simulation import simulate_inventory
from reorder_manager import calculate_reorder_recommendation

try:
    from alert_manager import get_inventory_alerts
except ImportError:
    get_inventory_alerts = None
import numpy as np
import pandas as pd
import joblib
import streamlit as st

from datetime import date

from login import show_login

from supplier_manager import (
    init_supplier_database,
    get_suppliers,
    add_supplier,
    update_supplier,
    delete_supplier
)

from medicine_manager import (
    init_database,
    seed_medicines,
    get_medicines,
    add_medicine,
    update_medicine,
    delete_medicine,
    get_supplier_names
)

from inventory_manager import (
    init_inventory_database,
    add_transaction,
    get_transactions,
    get_stock_summary
)


# =========================================================
# PATHS
# =========================================================

BASE = Path(__file__).parent
DATA = BASE / "data/medicine_sales.csv"
MODELS = BASE / "models"


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Medicine Stock-Out AI",
    page_icon="💊",
    layout="wide"
)


# =========================================================
# AUTHENTICATION
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


if not st.session_state.logged_in:

    show_login()

    st.stop()


# =========================================================
# LOGGED-IN USER
# =========================================================

username = st.session_state.get(
    "username",
    "User"
)

role = st.session_state.get(
    "role",
    "Pharmacy Staff"
)


st.sidebar.success(
    f"👤 {username}"
)

st.sidebar.caption(
    f"Role: {role}"
)


# =========================================================
# LOGOUT
# =========================================================

if st.sidebar.button("🚪 Logout"):

    st.session_state.logged_in = False

    st.session_state.pop(
        "username",
        None
    )

    st.session_state.pop(
        "role",
        None
    )

    st.rerun()


# =========================================================
# DATABASE
# =========================================================

init_database()

seed_medicines()

init_supplier_database()


# =========================================================
# LOAD DATA
# =========================================================

@st.cache_data
def load_data():

    return pd.read_csv(
        DATA,
        parse_dates=["date"]
    )


@st.cache_resource
def load_models():

    return (
        joblib.load(
            MODELS / "demand_model.pkl"
        ),

        joblib.load(
            MODELS / "stockout_model.pkl"
        )
    )


df = load_data()

demand_model, risk_model = load_models()


# =========================================================
# MODEL FEATURES
# =========================================================

DEMAND_FEATURES = [
    "lag_1",
    "lag_7",
    "rolling_7",
    "rolling_14",
    "rolling_30",
    "month",
    "day_of_week",
    "holiday",
    "closing_stock",
    "lead_time_days"
]


RISK_FEATURES = [
    "closing_stock",
    "rolling_7",
    "rolling_14",
    "rolling_30",
    "lead_time_days",
    "demand_std",
    "supplier_delay_rate"
]


# =========================================================
# TITLE
# =========================================================

st.title(
    "💊 Medicine Stock-Out Prediction & Intelligent Inventory"
)

st.caption(
    f"Logged in as: {username} | Role: {role}"
)

st.caption(
    "Machine Learning decision-support prototype — "
    "not a medical recommendation system."
)


# =========================================================
# SIDEBAR MEDICINE SELECTION
# =========================================================

st.sidebar.header(
    "Medicine Selection"
)

medicine = st.sidebar.selectbox(
    "Select medicine",
    sorted(
        df["medicine_name"].unique()
    )
)


# =========================================================
# ADMIN MENU
# =========================================================

if role == "Admin":

    st.sidebar.divider()
    st.sidebar.subheader("⚙️ Admin")

    admin_module = st.sidebar.selectbox(
        "Select Admin Module",
        [
            "None",
            "Manage Medicines",
            "Manage Suppliers",
            "Expiry Risk",
            "Inventory Management",
            "What-If Simulation",
            "Reorder Recommendation",
            "Alert Center"
        ],
        key="admin_module_select"
    )

else:
    admin_module = "None"


# =========================================================
# MEDICINE DATA
# =========================================================

m = df[
    df["medicine_name"] == medicine
].sort_values("date")


latest = m.iloc[-1]


# =========================================================
# MANAGE MEDICINES
# =========================================================

if (
    admin_module == "Manage Medicines"
    and role == "Admin"
):

    if st.session_state.get(
        "medicine_update_success",
        False
    ):

        st.success(
            "✅ Medicine updated successfully!"
        )

        st.session_state[
            "medicine_update_success"
        ] = False


    st.title(
        "💊 Manage Medicines"
    )

    st.caption(
        "Admin can add, edit and delete medicines."
    )


    # =====================================================
    # GET MEDICINES
    # =====================================================

    medicines_df = get_medicines()


    # =====================================================
    # ADD MEDICINE
    # =====================================================

    st.subheader(
        "➕ Add New Medicine"
    )


    with st.form(
        "add_medicine_form"
    ):

        col1, col2 = st.columns(2)


        with col1:

            new_name = st.text_input(
                "Medicine Name"
            )

            new_category = st.text_input(
                "Category",
                value="General"
            )

            new_unit = st.selectbox(
                "Unit",
                [
                    "tablets",
                    "capsules",
                    "strips",
                    "bottles",
                    "boxes",
                    "units"
                ]
            )

            # NEW
            new_batch_number = st.text_input(
                "Batch Number",
                placeholder="e.g. BATCH-001"
            )

            # NEW
            new_expiry_date = st.date_input(
                "Expiry Date",
                value=date.today()
            )


        with col2:

            new_minimum_stock = st.number_input(
                "Minimum Stock",
                min_value=0,
                value=100,
                step=10
            )


            supplier_list = get_supplier_names()


            if supplier_list:

                new_supplier = st.selectbox(
                    "Supplier",
                    supplier_list,
                    key="add_medicine_supplier"
                )

            else:

                new_supplier = st.text_input(
                    "Supplier",
                    value="Default Supplier",
                    key="add_medicine_supplier_text"
                )


            new_lead_time = st.number_input(
                "Lead Time (Days)",
                min_value=1,
                value=7,
                step=1
            )


        add_button = st.form_submit_button(
            "➕ Add Medicine",
            width="stretch"
        )


        if add_button:

            if not new_name.strip():

                st.warning(
                    "Please enter medicine name."
                )

            else:

                success, message = add_medicine(
                    new_name,
                    new_category,
                    new_unit,
                    new_minimum_stock,
                    new_supplier,
                    new_lead_time,
                    new_expiry_date.isoformat(),
                    new_batch_number
                )


                if success:

                    st.success(
                        "✅ Medicine added successfully!"
                    )

                    st.rerun()

                else:

                    st.error(
                        f"❌ {message}"
                    )


    st.divider()


    # =====================================================
    # CURRENT MEDICINES
    # =====================================================

    st.subheader(
        "📋 Medicine Inventory"
    )


    if medicines_df.empty:

        st.info(
            "No medicines found."
        )

    else:

        search = st.text_input(
            "🔍 Search medicine",
            placeholder="Enter medicine name..."
        )


        if search.strip():

            display_df = medicines_df[
                medicines_df["name"].str.contains(
                    search,
                    case=False,
                    na=False
                )
            ]

        else:

            display_df = medicines_df


        st.dataframe(
            display_df,
            width="stretch",
            hide_index=True
        )


    st.divider()


    # =====================================================
    # EDIT MEDICINE
    # =====================================================

    st.subheader(
        "✏️ Edit Medicine"
    )


    if not medicines_df.empty:

        medicine_options = medicines_df[
            "name"
        ].tolist()


        selected_name = st.selectbox(
            "Select medicine to edit",
            medicine_options,
            key="edit_medicine_select"
        )


        selected_row = medicines_df[
            medicines_df["name"] == selected_name
        ].iloc[0]


        with st.form(
            "edit_medicine_form"
        ):

            col1, col2 = st.columns(2)


            with col1:

                edit_name = st.text_input(
                    "Medicine Name",
                    value=selected_row["name"]
                )


                edit_category = st.text_input(
                    "Category",
                    value=selected_row["category"]
                )


                units = [
                    "tablets",
                    "capsules",
                    "strips",
                    "bottles",
                    "boxes",
                    "units"
                ]


                current_unit = selected_row["unit"]


                if current_unit in units:

                    unit_index = units.index(
                        current_unit
                    )

                else:

                    unit_index = 0


                edit_unit = st.selectbox(
                    "Unit",
                    units,
                    index=unit_index
                )


                # NEW
                current_batch = str(
                    selected_row["batch_number"]
                    if pd.notna(
                        selected_row["batch_number"]
                    )
                    else ""
                )


                edit_batch_number = st.text_input(
                    "Batch Number",
                    value=current_batch
                )


            with col2:

                edit_minimum_stock = st.number_input(
                    "Minimum Stock",
                    min_value=0,
                    value=int(
                        selected_row["minimum_stock"]
                    ),
                    step=10
                )


                supplier_list = get_supplier_names()


                current_supplier = str(
                    selected_row["supplier"]
                )


                if supplier_list:

                    if current_supplier in supplier_list:

                        supplier_index = supplier_list.index(
                            current_supplier
                        )

                    else:

                        supplier_index = 0


                    edit_supplier = st.selectbox(
                        "Supplier",
                        supplier_list,
                        index=supplier_index,
                        key="edit_medicine_supplier"
                    )

                else:

                    edit_supplier = st.text_input(
                        "Supplier",
                        value=current_supplier,
                        key="edit_medicine_supplier_text"
                    )


                edit_lead_time = st.number_input(
                    "Lead Time (Days)",
                    min_value=1,
                    value=int(
                        selected_row["lead_time_days"]
                    ),
                    step=1
                )


                # NEW
                current_expiry = str(
                    selected_row["expiry_date"]
                    if pd.notna(
                        selected_row["expiry_date"]
                    )
                    else ""
                )


                try:

                    expiry_value = (
                        pd.to_datetime(
                            current_expiry
                        ).date()
                        if current_expiry
                        else date.today()
                    )

                except:

                    expiry_value = date.today()


                edit_expiry_date = st.date_input(
                    "Expiry Date",
                    value=expiry_value
                )


            update_button = st.form_submit_button(
                "💾 Update Medicine",
                width="stretch"
            )


            if update_button:

                if not edit_name.strip():

                    st.warning(
                        "Please enter medicine name."
                    )

                else:

                    success, message = update_medicine(
                        selected_row["id"],
                        edit_name,
                        edit_category,
                        edit_unit,
                        edit_minimum_stock,
                        edit_supplier,
                        edit_lead_time,
                        edit_expiry_date.isoformat(),
                        edit_batch_number
                    )


                    if success:

                        st.session_state[
                            "medicine_update_success"
                        ] = True

                        st.rerun()

                    else:

                        st.error(
                            f"❌ {message}"
                        )


    st.divider()


    # =====================================================
    # DELETE MEDICINE
    # =====================================================

    st.subheader(
        "🗑️ Delete Medicine"
    )


    if not medicines_df.empty:

        delete_name = st.selectbox(
            "Select medicine to delete",
            medicines_df["name"].tolist(),
            key="delete_medicine_select"
        )


        delete_row = medicines_df[
            medicines_df["name"] == delete_name
        ].iloc[0]


        st.warning(
            f"You are about to delete **{delete_name}**."
        )


        confirm_delete = st.checkbox(
            "I confirm that I want to delete this medicine.",
            key="confirm_delete"
        )


        if st.button(
            "🗑️ Delete Medicine",
            disabled=not confirm_delete,
            key="delete_medicine_button"
        ):

            delete_medicine(
                delete_row["id"]
            )


            st.success(
                f"✅ {delete_name} deleted successfully."
            )


            st.rerun()


    st.stop()


# =========================================================
# EXPIRY RISK
# =========================================================

if (
    admin_module == "Expiry Risk"
    and role == "Admin"
):

    st.title(
        "📅 Medicine Expiry Risk"
    )

    st.caption(
        "Monitor medicine batches based on their expiry dates."
    )


    expiry_df = get_medicines().copy()


    if expiry_df.empty:

        st.info(
            "No medicines available."
        )

        st.stop()


    today = pd.Timestamp.today().normalize()


    expiry_df["expiry_date_parsed"] = pd.to_datetime(
        expiry_df["expiry_date"],
        errors="coerce"
    )


    expiry_df["days_to_expiry"] = (
        expiry_df["expiry_date_parsed"]
        - today
    ).dt.days


    def expiry_status(days):

        if pd.isna(days):

            return "NO DATE ⚪"

        if days < 0:

            return "EXPIRED 🔴"

        if days <= 30:

            return "CRITICAL 🔴"

        if days <= 90:

            return "WARNING 🟠"

        if days <= 180:

            return "MONITOR 🟡"

        return "SAFE 🟢"


    expiry_df["expiry_risk"] = (
        expiry_df["days_to_expiry"]
        .apply(expiry_status)
    )


    total_medicines = len(
        expiry_df
    )


    expired_count = int(
        (
            expiry_df["expiry_risk"]
            == "EXPIRED 🔴"
        ).sum()
    )


    critical_count = int(
        (
            expiry_df["expiry_risk"]
            == "CRITICAL 🔴"
        ).sum()
    )


    warning_count = int(
        (
            expiry_df["expiry_risk"]
            == "WARNING 🟠"
        ).sum()
    )


    safe_count = int(
        (
            expiry_df["expiry_risk"]
            == "SAFE 🟢"
        ).sum()
    )


    c1, c2, c3, c4 = st.columns(4)


    c1.metric(
        "Total Medicines",
        total_medicines
    )


    c2.metric(
        "Expired",
        expired_count
    )


    c3.metric(
        "Critical ≤ 30 Days",
        critical_count
    )


    c4.metric(
        "Safe",
        safe_count
    )


    st.divider()


    st.subheader(
        "📋 Expiry Monitoring"
    )


    display_expiry = expiry_df[
        [
            "name",
            "batch_number",
            "expiry_date",
            "days_to_expiry",
            "expiry_risk",
            "supplier"
        ]
    ].copy()


    display_expiry = display_expiry.rename(
        columns={
            "name": "Medicine",
            "batch_number": "Batch Number",
            "expiry_date": "Expiry Date",
            "days_to_expiry": "Days to Expiry",
            "expiry_risk": "Risk",
            "supplier": "Supplier"
        }
    )


    st.dataframe(
        display_expiry,
        width="stretch",
        hide_index=True
    )


    st.divider()


    st.subheader(
        "⚠️ Expiry Alerts"
    )


    alerts = expiry_df[
        expiry_df["expiry_risk"].isin(
            [
                "EXPIRED 🔴",
                "CRITICAL 🔴",
                "WARNING 🟠"
            ]
        )
    ]


    if alerts.empty:

        st.success(
            "✅ No medicines require expiry attention."
        )

    else:

        for _, row in alerts.iterrows():

            medicine_name = row["name"]

            batch = row["batch_number"]

            days = row["days_to_expiry"]


            if pd.isna(days):

                st.warning(
                    f"⚠️ {medicine_name} — expiry date missing."
                )

            elif days < 0:

                st.error(
                    f"🔴 {medicine_name} "
                    f"(Batch: {batch}) — expired."
                )

            else:

                st.warning(
                    f"⚠️ {medicine_name} "
                    f"(Batch: {batch}) — "
                    f"expires in {int(days)} days."
                )


    st.stop()

# =========================================================
# INVENTORY MANAGEMENT
# =========================================================

if (
    admin_module == "Inventory Management"
    and role == "Admin"
):

    init_inventory_database()

    st.title("📦 Inventory & Sales Management")
    st.caption(
        "Manage stock received, medicine sales and current inventory."
    )

    medicines_df = get_medicines()

    if medicines_df.empty:
        st.warning("Please add medicines first.")
        st.stop()

    # =====================================================
    # CURRENT STOCK SUMMARY
    # =====================================================

    st.subheader("📊 Current Stock")

    stock_df = get_stock_summary()

    if stock_df.empty:
        st.info("No inventory records found. Please add medicines first.")
    else:
        total_medicines = len(stock_df)
        total_stock = int(stock_df["current_stock"].sum())
        low_stock_count = int(
            (stock_df["current_stock"] <= stock_df["minimum_stock"]).sum()
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("💊 Total Medicines", total_medicines)
        c2.metric("📦 Total Stock", total_stock)
        c3.metric("⚠️ Low Stock Items", low_stock_count)

        display_stock = stock_df.copy()
        display_stock["Stock Status"] = display_stock.apply(
            lambda row: "🔴 LOW STOCK"
            if row["current_stock"] <= row["minimum_stock"]
            else "🟢 NORMAL",
            axis=1
        )

        st.dataframe(
            display_stock[
                [
                    "name", "category", "unit", "current_stock",
                    "minimum_stock", "Stock Status"
                ]
            ],
            width="stretch",
            hide_index=True
        )

    # =====================================================
    # ADD TRANSACTION
    # =====================================================

    st.divider()
    st.subheader("➕➖ Add Stock Transaction")

    medicine_options = medicines_df["name"].tolist()

    selected_medicine = st.selectbox(
        "💊 Select Medicine",
        medicine_options,
        key="inventory_medicine_select"
    )

    selected_row = medicines_df[
        medicines_df["name"] == selected_medicine
    ].iloc[0]

    transaction_type = st.radio(
        "Transaction Type",
        ["STOCK_IN", "SALE"],
        horizontal=True,
        key="inventory_transaction_type"
    )

    if transaction_type == "STOCK_IN":
        st.info("➕ Stock Received")
    else:
        st.info("➖ Units Sold")

    quantity = st.number_input(
        "Quantity",
        min_value=1,
        value=1,
        step=1,
        key="inventory_quantity"
    )

    transaction_date = st.date_input(
        "Transaction Date",
        value=date.today(),
        key="inventory_transaction_date"
    )

    batch_number = st.text_input(
        "Batch Number",
        key="inventory_batch_number",
        placeholder="e.g. BATCH-001"
    )

    notes = st.text_input(
        "Notes",
        key="inventory_notes",
        placeholder="Optional notes"
    )

    if st.button(
        "💾 Save Transaction",
        type="primary",
        width="stretch",
        key="save_inventory_transaction"
    ):

        current_stock_df = get_stock_summary()
        current_row = current_stock_df[
            current_stock_df["id"] == selected_row["id"]
        ]

        current_quantity = (
            int(current_row["current_stock"].iloc[0])
            if not current_row.empty
            else 0
        )

        if (
            transaction_type == "SALE"
            and quantity > current_quantity
        ):
            st.error(
                f"❌ Sale quantity cannot exceed current stock "
                f"({current_quantity})."
            )
        else:
            success, message = add_transaction(
                selected_row["id"],
                transaction_type,
                quantity,
                transaction_date.isoformat(),
                batch_number,
                notes
            )

            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    # =====================================================
    # TRANSACTION HISTORY
    # =====================================================

    st.divider()
    st.subheader("📋 Stock Movement History")

    transactions_df = get_transactions()

    if transactions_df.empty:
        st.info("No inventory transactions recorded yet.")
    else:
        st.dataframe(
            transactions_df[
                [
                    "medicine", "transaction_type", "quantity",
                    "transaction_date", "batch_number", "notes"
                ]
            ],
            width="stretch",
            hide_index=True
        )

    # =====================================================
    # LOW STOCK ALERTS
    # =====================================================

    if not stock_df.empty:
        low_stock = stock_df[
            stock_df["current_stock"] <= stock_df["minimum_stock"]
        ]

        if not low_stock.empty:
            st.divider()
            st.subheader("⚠️ Low Stock Alerts")

            for _, row in low_stock.iterrows():
                st.warning(
                    f"⚠️ **{row['name']}** — Current stock: "
                    f"{int(row['current_stock'])} {row['unit']} | "
                    f"Minimum required: {int(row['minimum_stock'])}"
                )

    st.stop()

# =========================================================
# WHAT-IF INVENTORY SIMULATION
# =========================================================

if (
    admin_module == "What-If Simulation"
    and role == "Admin"
):

    st.title("🔮 What-If Inventory Simulation")

    st.caption(
        "Scenario analysis to understand how changes in expected sales "
        "may affect medicine inventory."
    )

    medicines_df = get_medicines()

    if medicines_df.empty:

        st.warning(
            "Please add medicines first."
        )

        st.stop()

    # =====================================================
    # SELECT MEDICINE
    # =====================================================

    st.subheader("💊 Select Medicine")

    medicine_options = medicines_df["name"].tolist()

    selected_medicine = st.selectbox(
        "Medicine",
        medicine_options,
        key="simulation_medicine"
    )

    selected_row = medicines_df[
        medicines_df["name"] == selected_medicine
    ].iloc[0]

    medicine_id = int(selected_row["id"])

    # =====================================================
    # CURRENT STOCK
    # =====================================================

    stock_df = get_stock_summary()

    stock_row = stock_df[
        stock_df["id"] == medicine_id
    ]

    if stock_row.empty:

        current_stock = 0

    else:

        current_stock = int(
            stock_row["current_stock"].iloc[0]
        )

    # =====================================================
    # DAILY DEMAND
    # =====================================================

    transactions_df = get_transactions()

    medicine_sales = transactions_df[
        (transactions_df["medicine_id"] == medicine_id)
        &
        (transactions_df["transaction_type"] == "SALE")
    ].copy()

    if medicine_sales.empty:

        daily_demand = 1.0

        st.info(
            "No sales history available. "
            "A default demand of 1 unit/day is being used."
        )

    else:

        total_sales = medicine_sales["quantity"].sum()

        dates = pd.to_datetime(
            medicine_sales["transaction_date"]
        )

        date_range = (
            dates.max() - dates.min()
        ).days

        days = max(date_range, 1)

        daily_demand = total_sales / days

    # =====================================================
    # CURRENT INFORMATION
    # =====================================================

    st.subheader("📊 Current Situation")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Current Stock",
        f"{current_stock} units"
    )

    c2.metric(
        "Estimated Daily Demand",
        f"{daily_demand:.1f} units"
    )

    c3.metric(
        "Minimum Stock",
        f"{int(selected_row['minimum_stock'])} units"
    )

    # =====================================================
    # SALES SCENARIO
    # =====================================================

    st.divider()

    st.subheader("🎯 Sales Scenario")

    sales_change = st.slider(
        "Change in Expected Sales (%)",
        min_value=-50,
        max_value=100,
        value=0,
        step=10,
        key="simulation_sales_change"
    )

    if sales_change > 0:

        st.warning(
            f"📈 Expected sales increase by {sales_change}%"
        )

    elif sales_change < 0:

        st.info(
            f"📉 Expected sales decrease by {abs(sales_change)}%"
        )

    else:

        st.info(
            "➡️ No change in expected sales"
        )

    # =====================================================
    # RUN SIMULATION
    # =====================================================

    result = simulate_inventory(
        current_stock,
        daily_demand,
        sales_change
    )

    adjusted_demand = result[
        "adjusted_demand"
    ]

    days_until_stockout = result[
        "days_until_stockout"
    ]

    remaining_stock = result[
        "remaining_stock"
    ]

    # =====================================================
    # RESULTS
    # =====================================================

    st.divider()

    st.subheader("🔍 Simulation Result")

    r1, r2, r3 = st.columns(3)

    r1.metric(
        "Adjusted Daily Demand",
        f"{adjusted_demand:.1f} units"
    )

    r2.metric(
        "Estimated Days Until Stockout",
        f"{days_until_stockout} days"
    )

    r3.metric(
        "Remaining Stock",
        f"{remaining_stock:.0f} units"
    )

    # =====================================================
    # DECISION SUPPORT
    # =====================================================

    st.divider()

    if current_stock <= 0:

        st.error(
            "🔴 CRITICAL: Current stock is already zero."
        )

    elif days_until_stockout <= 3:

        st.error(
            "🔴 HIGH RISK: Stock may run out within 3 days."
        )

    elif days_until_stockout <= 7:

        st.warning(
            "🟠 WARNING: Stock may run out within 7 days."
        )

    else:

        st.success(
            "🟢 STOCK STATUS: Inventory appears sufficient "
            "under this scenario."
        )

    st.info(
        "💡 This is a What-If scenario analysis, not a guaranteed "
        "future prediction. It helps support inventory decisions."
    )

    st.stop()


# =========================================================
# REORDER RECOMMENDATION
# =========================================================

if (
    admin_module == "Reorder Recommendation"
    and role == "Admin"
):

    st.title("📦 AI Reorder Recommendation")

    st.caption(
        "Decision-support module that recommends when and how much "
        "medicine stock should be reordered."
    )

    medicines_df = get_medicines()

    if medicines_df.empty:

        st.warning(
            "Please add medicines first."
        )

        st.stop()

    # =====================================================
    # SELECT MEDICINE
    # =====================================================

    st.subheader("💊 Select Medicine")

    medicine_options = medicines_df["name"].tolist()

    selected_medicine = st.selectbox(
        "Medicine",
        medicine_options,
        key="reorder_medicine"
    )

    selected_row = medicines_df[
        medicines_df["name"] == selected_medicine
    ].iloc[0]

    medicine_id = int(selected_row["id"])

    # =====================================================
    # CURRENT STOCK
    # =====================================================

    stock_df = get_stock_summary()

    stock_row = stock_df[
        stock_df["id"] == medicine_id
    ]

    if stock_row.empty:

        current_stock = 0

    else:

        current_stock = int(
            stock_row["current_stock"].iloc[0]
        )

    # =====================================================
    # SALES DEMAND
    # =====================================================

    transactions_df = get_transactions()

    medicine_sales = transactions_df[
        (transactions_df["medicine_id"] == medicine_id)
        &
        (transactions_df["transaction_type"] == "SALE")
    ].copy()

    if medicine_sales.empty:

        daily_demand = 1.0

        st.info(
            "No sales history available. "
            "Default demand of 1 unit/day is being used."
        )

    else:

        total_sales = medicine_sales["quantity"].sum()

        dates = pd.to_datetime(
            medicine_sales["transaction_date"]
        )

        date_range = (
            dates.max() - dates.min()
        ).days

        days = max(date_range, 1)

        daily_demand = total_sales / days

    # =====================================================
    # LEAD TIME & MINIMUM STOCK
    # =====================================================

    lead_time_days = int(
        selected_row["lead_time_days"]
    )

    minimum_stock = int(
        selected_row["minimum_stock"]
    )

    # =====================================================
    # CURRENT INFORMATION
    # =====================================================

    st.subheader("📊 Current Inventory Information")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Current Stock",
        f"{current_stock}"
    )

    c2.metric(
        "Daily Demand",
        f"{daily_demand:.1f}"
    )

    c3.metric(
        "Lead Time",
        f"{lead_time_days} days"
    )

    c4.metric(
        "Minimum Stock",
        f"{minimum_stock}"
    )

    # =====================================================
    # SAFETY DAYS
    # =====================================================

    st.divider()

    st.subheader("🛡️ Safety Stock Settings")

    safety_days = st.slider(
        "Additional Safety Coverage (Days)",
        min_value=1,
        max_value=14,
        value=3,
        step=1,
        key="reorder_safety_days"
    )

    # =====================================================
    # CALCULATE RECOMMENDATION
    # =====================================================

    result = calculate_reorder_recommendation(
        current_stock=current_stock,
        daily_demand=daily_demand,
        lead_time_days=lead_time_days,
        minimum_stock=minimum_stock,
        safety_days=safety_days
    )

    lead_time_demand = result[
        "lead_time_demand"
    ]

    safety_stock = result[
        "safety_stock"
    ]

    reorder_point = result[
        "reorder_point"
    ]

    recommended_quantity = result[
        "recommended_quantity"
    ]

    decision = result[
        "decision"
    ]

    # =====================================================
    # REORDER CALCULATION
    # =====================================================

    st.divider()

    st.subheader("🔍 Reorder Analysis")

    r1, r2, r3 = st.columns(3)

    r1.metric(
        "Lead-Time Demand",
        f"{lead_time_demand:.1f} units"
    )

    r2.metric(
        "Safety Stock",
        f"{safety_stock:.1f} units"
    )

    r3.metric(
        "Reorder Point",
        f"{reorder_point:.1f} units"
    )

    # =====================================================
    # RECOMMENDATION
    # =====================================================

    st.divider()

    st.subheader("🤖 AI Recommendation")

    if decision == "REORDER NOW":

        st.error(
            f"🔴 REORDER NOW — Recommended order quantity: "
            f"{recommended_quantity} units"
        )

        st.write(
            f"Current stock ({current_stock} units) is below "
            f"the calculated reorder point "
            f"({reorder_point:.1f} units)."
        )

    else:

        st.success(
            "🟢 STOCK SUFFICIENT — No immediate reorder required."
        )

        st.write(
            f"Current stock ({current_stock} units) is above "
            f"the calculated reorder point "
            f"({reorder_point:.1f} units)."
        )

    # =====================================================
    # DECISION SUMMARY
    # =====================================================

    st.divider()

    st.subheader("📋 Decision Summary")

    summary_df = pd.DataFrame({
        "Parameter": [
            "Medicine",
            "Current Stock",
            "Daily Demand",
            "Lead Time",
            "Minimum Stock",
            "Safety Coverage",
            "Lead-Time Demand",
            "Safety Stock",
            "Reorder Point",
            "Recommended Order Quantity",
            "Decision"
        ],
        "Value": [
            selected_medicine,
            f"{current_stock} units",
            f"{daily_demand:.1f} units/day",
            f"{lead_time_days} days",
            f"{minimum_stock} units",
            f"{safety_days} days",
            f"{lead_time_demand:.1f} units",
            f"{safety_stock:.1f} units",
            f"{reorder_point:.1f} units",
            f"{recommended_quantity} units",
            decision
        ]
    })

    st.dataframe(
        summary_df,
        width="stretch",
        hide_index=True
    )

    st.info(
        "💡 This recommendation is a decision-support estimate "
        "based on current inventory and demand assumptions. "
        "It is not a guaranteed future prediction."
    )

    st.stop()


# =========================================================
# MANAGE SUPPLIERS
# =========================================================

if (
    admin_module == "Manage Suppliers"
    and role == "Admin"
):

    st.title(
        "🏢 Supplier Management"
    )

    st.caption(
        "Add, update, search and manage medicine suppliers."
    )


    if st.session_state.get(
        "supplier_update_success",
        False
    ):

        st.success(
            "✅ Supplier updated successfully!"
        )

        st.session_state[
            "supplier_update_success"
        ] = False


    # =====================================================
    # ADD SUPPLIER
    # =====================================================

    st.subheader(
        "➕ Add New Supplier"
    )


    with st.form(
        "add_supplier_form"
    ):

        col1, col2 = st.columns(2)


        with col1:

            supplier_name = st.text_input(
                "Supplier Name",
                placeholder="e.g. ABC Pharma"
            )


            contact_person = st.text_input(
                "Contact Person",
                placeholder="e.g. Rahul Sharma"
            )


            phone = st.text_input(
                "Phone",
                placeholder="e.g. 9876543210"
            )


            email = st.text_input(
                "Email",
                placeholder="supplier@example.com"
            )


        with col2:

            address = st.text_area(
                "Address",
                placeholder="Supplier address"
            )


            reliability = st.number_input(
                "Reliability (%)",
                min_value=0.0,
                max_value=100.0,
                value=90.0,
                step=1.0
            )


            average_lead_time = st.number_input(
                "Average Lead Time (Days)",
                min_value=1,
                max_value=365,
                value=7,
                step=1
            )


        add_button = st.form_submit_button(
            "➕ Add Supplier",
            width="stretch"
        )


        if add_button:

            if not supplier_name.strip():

                st.error(
                    "Supplier name is required."
                )

            else:

                success, message = add_supplier(
                    supplier_name,
                    contact_person,
                    phone,
                    email,
                    address,
                    reliability,
                    average_lead_time
                )


                if success:

                    st.success(
                        message
                    )

                    st.rerun()

                else:

                    st.error(
                        message
                    )


    st.divider()


    # =====================================================
    # SUPPLIER LIST
    # =====================================================

    st.subheader(
        "📋 Supplier List"
    )


    suppliers_df = get_suppliers()


    if suppliers_df.empty:

        st.info(
            "No suppliers found. Add your first supplier above."
        )

    else:

        search_supplier = st.text_input(
            "🔍 Search Supplier",
            placeholder="Search by supplier name, contact or phone"
        )


        filtered_suppliers = suppliers_df.copy()


        if search_supplier.strip():

            search_text = (
                search_supplier
                .strip()
                .lower()
            )


            filtered_suppliers = (
                filtered_suppliers[
                    filtered_suppliers.astype(str)
                    .apply(
                        lambda row:
                        row.str.lower()
                        .str.contains(
                            search_text,
                            na=False
                        )
                        .any(),
                        axis=1
                    )
                ]
            )


        st.dataframe(
            filtered_suppliers,
            width="stretch",
            hide_index=True
        )


    st.divider()


    # =====================================================
    # EDIT SUPPLIER
    # =====================================================

    st.subheader(
        "✏️ Edit Supplier"
    )


    suppliers_df = get_suppliers()


    if not suppliers_df.empty:

        supplier_options = {

            f"{row['name']} (ID: {row['id']})":
            row["id"]

            for _, row in suppliers_df.iterrows()

        }


        selected_supplier_label = st.selectbox(
            "Select Supplier",
            list(
                supplier_options.keys()
            ),
            key="edit_supplier_select"
        )


        selected_supplier_id = (
            supplier_options[
                selected_supplier_label
            ]
        )


        selected_supplier = suppliers_df[
            suppliers_df["id"] ==
            selected_supplier_id
        ].iloc[0]


        with st.form(
            "edit_supplier_form"
        ):

            col1, col2 = st.columns(2)


            with col1:

                edit_name = st.text_input(
                    "Supplier Name",
                    value=str(
                        selected_supplier["name"]
                    )
                )


                edit_contact = st.text_input(
                    "Contact Person",
                    value=str(
                        selected_supplier[
                            "contact_person"
                        ]
                    )
                )


                edit_phone = st.text_input(
                    "Phone",
                    value=str(
                        selected_supplier["phone"]
                    )
                )


                edit_email = st.text_input(
                    "Email",
                    value=str(
                        selected_supplier["email"]
                    )
                )


            with col2:

                edit_address = st.text_area(
                    "Address",
                    value=str(
                        selected_supplier["address"]
                    )
                )


                edit_reliability = st.number_input(
                    "Reliability (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(
                        selected_supplier[
                            "reliability"
                        ]
                    ),
                    step=1.0
                )


                edit_lead_time = st.number_input(
                    "Average Lead Time (Days)",
                    min_value=1,
                    max_value=365,
                    value=int(
                        selected_supplier[
                            "average_lead_time"
                        ]
                    ),
                    step=1
                )


            update_button = st.form_submit_button(
                "💾 Update Supplier",
                width="stretch"
            )


            if update_button:

                success, message = update_supplier(
                    selected_supplier_id,
                    edit_name,
                    edit_contact,
                    edit_phone,
                    edit_email,
                    edit_address,
                    edit_reliability,
                    edit_lead_time
                )


                if success:

                    st.session_state[
                        "supplier_update_success"
                    ] = True

                    st.rerun()

                else:

                    st.error(
                        message
                    )


    st.divider()


    # =====================================================
    # DELETE SUPPLIER
    # =====================================================

    st.subheader(
        "🗑️ Delete Supplier"
    )


    suppliers_df = get_suppliers()


    if not suppliers_df.empty:

        delete_options = {

            f"{row['name']} (ID: {row['id']})":
            row["id"]

            for _, row in suppliers_df.iterrows()

        }


        selected_delete_label = st.selectbox(
            "Select Supplier to Delete",
            list(
                delete_options.keys()
            ),
            key="delete_supplier_select"
        )


        selected_delete_id = (
            delete_options[
                selected_delete_label
            ]
        )


        confirm_supplier_delete = st.checkbox(
            "I confirm that I want to delete this supplier.",
            key="confirm_supplier_delete"
        )


        if st.button(
            "🗑️ Delete Supplier",
            disabled=not confirm_supplier_delete,
            width="stretch",
            key="delete_supplier_button"
        ):

            delete_supplier(
                selected_delete_id
            )


            st.success(
                "✅ Supplier deleted successfully!"
            )


            st.rerun()


    st.stop()


# =========================================================
# ALERT CENTER
# =========================================================

if (
    admin_module == "Alert Center"
    and role == "Admin"
):

    st.title("🚨 Inventory Alert Center")
    st.caption(
        "Central view of low-stock, expiry and reorder-related alerts."
    )

    medicines_df = get_medicines().copy()
    stock_df = get_stock_summary().copy()

    if medicines_df.empty:
        st.info("No medicines available.")
        st.stop()

    # -----------------------------------------------------
    # LOW STOCK ALERTS
    # -----------------------------------------------------

    low_stock = stock_df[
        stock_df["current_stock"] <= stock_df["minimum_stock"]
    ].copy() if not stock_df.empty else pd.DataFrame()

    # -----------------------------------------------------
    # EXPIRY ALERTS
    # -----------------------------------------------------

    medicines_df["expiry_date_parsed"] = pd.to_datetime(
        medicines_df["expiry_date"],
        errors="coerce"
    )

    today = pd.Timestamp.today().normalize()
    medicines_df["days_to_expiry"] = (
        medicines_df["expiry_date_parsed"] - today
    ).dt.days

    expiry_alerts = medicines_df[
        medicines_df["days_to_expiry"].notna()
        & (medicines_df["days_to_expiry"] <= 30)
    ].copy()

    # -----------------------------------------------------
    # ALERT SUMMARY
    # -----------------------------------------------------

    expired_count = int(
        (medicines_df["days_to_expiry"] < 0).sum()
    )
    expiry_30_count = int(
        (
            (medicines_df["days_to_expiry"] >= 0)
            & (medicines_df["days_to_expiry"] <= 30)
        ).sum()
    )
    low_stock_count = len(low_stock)

    c1, c2, c3 = st.columns(3)
    c1.metric("🔴 Expired", expired_count)
    c2.metric("📅 Expiring ≤ 30 Days", expiry_30_count)
    c3.metric("📦 Low Stock", low_stock_count)

    st.divider()

    # -----------------------------------------------------
    # LOW STOCK SECTION
    # -----------------------------------------------------

    st.subheader("📦 Low Stock Alerts")

    if low_stock.empty:
        st.success("✅ No low-stock medicines.")
    else:
        for _, row in low_stock.iterrows():
            st.warning(
                f"⚠️ **{row['name']}** — "
                f"Current: {int(row['current_stock'])} {row['unit']} | "
                f"Minimum: {int(row['minimum_stock'])}"
            )

    # -----------------------------------------------------
    # EXPIRY SECTION
    # -----------------------------------------------------

    st.divider()
    st.subheader("📅 Expiry Alerts")

    if expiry_alerts.empty:
        st.success("✅ No medicines are expired or expiring within 30 days.")
    else:
        for _, row in expiry_alerts.iterrows():
            days = int(row["days_to_expiry"])
            batch = row.get("batch_number", "")

            if days < 0:
                st.error(
                    f"🔴 **{row['name']}** (Batch: {batch}) — EXPIRED."
                )
            else:
                st.warning(
                    f"🟠 **{row['name']}** (Batch: {batch}) — "
                    f"expires in {days} days."
                )

    # -----------------------------------------------------
    # OPTIONAL ALERT MANAGER OUTPUT
    # -----------------------------------------------------

    if get_inventory_alerts is not None:
        try:
            generated_alerts = get_inventory_alerts()
            if generated_alerts:
                st.divider()
                st.subheader("🤖 System Alerts")
                if isinstance(generated_alerts, (list, tuple)):
                    for alert in generated_alerts:
                        st.info(str(alert))
                else:
                    st.info(str(generated_alerts))
        except TypeError:
            # Different alert_manager signatures are handled safely.
            pass
        except Exception:
            pass

    st.info(
        "💡 Alerts are decision-support indicators. Verify stock, batch "
        "and expiry information before taking purchasing or dispensing actions."
    )

    st.stop()


# =========================================================
# NORMAL DASHBOARD
# =========================================================

high_risk_count = int(
    (
        df["stockout_risk"] == 1
    ).sum()
)


low_stock_count = int(
    (
        df["closing_stock"]
        <
        df["rolling_7"] * 5
    ).sum()
)


# =========================================================
# KPI CARDS
# =========================================================

c1, c2, c3, c4 = st.columns(4)


c1.metric(
    "Medicines",
    df["medicine_name"].nunique()
)


c2.metric(
    "Latest Stock",
    int(
        latest["closing_stock"]
    )
)


c3.metric(
    "High-Risk Records",
    high_risk_count
)


c4.metric(
    "Low-Stock Records",
    low_stock_count
)


st.divider()


# =========================================================
# CURRENT MEDICINE INFO
# =========================================================

st.subheader(
    f"🔎 {medicine}"
)


info1, info2, info3, info4 = st.columns(4)


info1.metric(
    "Current Stock",
    f'{int(latest["closing_stock"])} units'
)


info2.metric(
    "7-Day Avg Demand",
    f'{latest["rolling_7"]:.1f}'
)


info3.metric(
    "Lead Time",
    f'{int(latest["lead_time_days"])} days'
)


info4.metric(
    "Demand Std.",
    f'{latest["demand_std"]:.1f}'
)


# =========================================================
# FORECAST NEXT 7 DAYS
# =========================================================

history = m.copy()

predictions = []

current_date = latest["date"]


for i in range(7):

    sales = history[
        "units_sold"
    ].tolist()


    lag1 = sales[-1]


    lag7 = (
        sales[-7]
        if len(sales) >= 7
        else np.mean(sales)
    )


    r7 = np.mean(
        sales[-7:]
    )


    r14 = (
        np.mean(
            sales[-14:]
        )
        if len(sales) >= 14
        else r7
    )


    r30 = (
        np.mean(
            sales[-30:]
        )
        if len(sales) >= 30
        else np.mean(sales)
    )


    future_date = (
        current_date
        +
        pd.Timedelta(
            days=i + 1
        )
    )


    month = future_date.month

    dow = future_date.dayofweek


    row = pd.DataFrame([{

        "lag_1": lag1,

        "lag_7": lag7,

        "rolling_7": r7,

        "rolling_14": r14,

        "rolling_30": r30,

        "month": month,

        "day_of_week": dow,

        "holiday": 0,

        "closing_stock": max(
            0,
            latest["closing_stock"]
            -
            sum(predictions)
        ),

        "lead_time_days":
            latest["lead_time_days"]

    }])


    pred = max(
        0,
        float(
            demand_model.predict(
                row[DEMAND_FEATURES]
            )[0]
        )
    )


    predictions.append(
        pred
    )


# =========================================================
# FORECAST DATAFRAME
# =========================================================

forecast = pd.DataFrame({

    "Date": [

        current_date
        +
        pd.Timedelta(
            days=i + 1
        )

        for i in range(7)

    ],

    "Predicted Demand":
        np.round(
            predictions,
            1
        )

})


# =========================================================
# INVENTORY CALCULATIONS
# =========================================================

total_7 = float(
    forecast[
        "Predicted Demand"
    ].sum()
)


current_stock = float(
    latest["closing_stock"]
)


lead_time = int(
    latest["lead_time_days"]
)


daily_avg = max(
    float(
        latest["rolling_7"]
    ),
    0.1
)


safety_stock = (
    1.65
    *
    float(
        latest["demand_std"]
    )
    *
    np.sqrt(
        max(
            lead_time,
            1
        )
    )
)


reorder_point = (
    daily_avg
    *
    lead_time
    +
    safety_stock
)


target_stock = (
    daily_avg
    *
    (
        lead_time + 7
    )
    +
    safety_stock
)


reorder_qty = max(
    0,
    int(
        np.ceil(
            target_stock
            -
            current_stock
        )
    )
)


# =========================================================
# ETA
# =========================================================

cum = forecast[
    "Predicted Demand"
].cumsum()


hit = np.where(
    cum >= current_stock
)[0]


eta_days = (
    int(
        hit[0] + 1
    )
    if len(hit)
    else None
)


# =========================================================
# RISK MODEL
# =========================================================

risk_row = pd.DataFrame([{

    "closing_stock":
        latest["closing_stock"],

    "rolling_7":
        latest["rolling_7"],

    "rolling_14":
        latest["rolling_14"],

    "rolling_30":
        latest["rolling_30"],

    "lead_time_days":
        latest["lead_time_days"],

    "demand_std":
        latest["demand_std"],

    "supplier_delay_rate":
        latest["supplier_delay_rate"]

}])


risk_prob = float(
    risk_model.predict_proba(
        risk_row[
            RISK_FEATURES
        ]
    )[0][1]
)


if risk_prob >= 0.75:

    risk = "CRITICAL 🔴"

elif risk_prob >= 0.50:

    risk = "HIGH 🟠"

elif risk_prob >= 0.25:

    risk = "MEDIUM 🟡"

else:

    risk = "LOW 🟢"


# =========================================================
# DEMAND FORECAST
# =========================================================

st.subheader(
    "📈 7-Day Demand Forecast"
)


st.line_chart(
    forecast.set_index(
        "Date"
    )[
        "Predicted Demand"
    ]
)


a, b, c, d = st.columns(4)


a.metric(
    "7-Day Forecast",
    f"{total_7:.0f} units"
)


b.metric(
    "Stock-Out Risk",
    risk
)


c.metric(
    "Risk Probability",
    f"{risk_prob * 100:.1f}%"
)


d.metric(
    "Recommended Order",
    f"{reorder_qty} units"
)


# =========================================================
# ETA MESSAGE
# =========================================================

if eta_days:

    st.error(
        "⚠️ Estimated stock-out within approximately "
        f"{eta_days} day(s) under the forecast scenario."
    )

else:

    st.success(
        "✅ Current forecast does not exhaust "
        "the available stock within 7 days."
    )


# =========================================================
# RISK EXPLANATION
# =========================================================

st.subheader(
    "🧠 Why is the risk high/low?"
)


reasons = []


if current_stock < total_7:

    reasons.append(
        "Current stock is lower than predicted 7-day demand."
    )


if (
    daily_avg > 0
    and
    current_stock / daily_avg
    <
    lead_time
):

    reasons.append(
        "Available inventory is below expected "
        "lead-time consumption."
    )


if (
    latest["demand_std"]
    >
    daily_avg * 0.5
):

    reasons.append(
        "Demand is relatively volatile."
    )


if latest["lead_time_days"] >= 7:

    reasons.append(
        "Supplier lead time is relatively long."
    )


if not reasons:

    reasons.append(
        "Current inventory is adequate relative "
        "to recent demand and lead time."
    )


for r in reasons:

    st.write(
        "• " + r
    )


# =========================================================
# INVENTORY DECISION
# =========================================================

st.subheader(
    "📦 Inventory Decision"
)


decision = (
    "ORDER NOW"
    if current_stock <= reorder_point
    else "MONITOR"
)


if decision == "ORDER NOW":

    st.warning(
        f"**{decision}** — "
        f"Suggested quantity: "
        f"**{reorder_qty} units**"
    )

else:

    st.info(
        f"**{decision}** — "
        "Stock is currently above "
        "the calculated reorder point."
    )


# =========================================================
# HISTORICAL SALES
# =========================================================

st.subheader(
    "📊 Historical Sales"
)


chart = m.tail(90).set_index(
    "date"
)[
    ["units_sold"]
]


st.bar_chart(
    chart
)


# =========================================================
# LATEST RECORDS
# =========================================================

st.subheader(
    "📋 Latest Records"
)


st.dataframe(
    m.tail(20)[
        [
            "date",
            "medicine_name",
            "units_sold",
            "received_qty",
            "closing_stock",
            "stockout"
        ]
    ].sort_values(
        "date",
        ascending=False
    ),
    width="stretch"
)


# =========================================================
# MODEL EVALUATION
# =========================================================

with st.expander(
    "Model evaluation"
):

    metrics_file = (
        MODELS / "metrics.json"
    )


    if metrics_file.exists():

        metrics = json.loads(
            metrics_file.read_text()
        )

        st.json(
            metrics
        )


    st.write(
        "The prototype uses a chronological "
        "train/test split. For a production system, "
        "validate on real pharmacy/hospital data "
        "before deployment."
    )