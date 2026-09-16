import numpy as np
import pandas as pd
from pathlib import Path

OUT = Path("data/medicine_sales.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)

rng = np.random.default_rng(42)

medicines = [
    ("MED001","Paracetamol 500mg","Analgesic",3.0,4,120),
    ("MED002","Amoxicillin 500mg","Antibiotic",8.0,6,90),
    ("MED003","Azithromycin 500mg","Antibiotic",12.0,5,70),
    ("MED004","Cetirizine 10mg","Antihistamine",2.5,3,100),
    ("MED005","Omeprazole 20mg","Gastro",4.0,4,110),
    ("MED006","Metformin 500mg","Diabetes",3.5,7,130),
    ("MED007","Amlodipine 5mg","Cardiac",2.8,7,125),
    ("MED008","ORS Sachet","Rehydration",5.0,3,80),
    ("MED009","Ibuprofen 400mg","Analgesic",4.5,5,75),
    ("MED010","Pantoprazole 40mg","Gastro",6.0,4,85),
    ("MED011","Levocetirizine 5mg","Antihistamine",3.5,3,65),
    ("MED012","Cough Syrup 100ml","Cold/Cough",65.0,4,55),
    ("MED013","Vitamin D3","Supplement",7.0,8,60),
    ("MED014","Salbutamol","Respiratory",18.0,6,50),
    ("MED015","Insulin","Critical",45.0,8,45),
    ("MED016","Diclofenac","Analgesic",5.0,5,60),
    ("MED017","Ranitidine Substitute","Gastro",3.0,4,55),
    ("MED018","Multivitamin","Supplement",6.0,5,70),
    ("MED019","Montelukast","Respiratory",9.0,6,65),
    ("MED020","Antiseptic Solution","First Aid",35.0,4,50),
]

dates = pd.date_range("2025-01-01", "2025-12-31", freq="D")
rows = []

for mid, name, category, price, lead, base_demand in medicines:
    stock = int(base_demand * (lead + 4) * 1.25)
    for d in dates:
        dow = d.dayofweek
        month = d.month

        seasonal = 1.0
        if category in ["Cold/Cough","Antihistamine","Respiratory"]:
            seasonal += 0.35 if month in [11,12,1,2] else 0.05
        if category == "Rehydration":
            seasonal += 0.35 if month in [4,5,6,7] else 0.0
        if category == "Analgesic":
            seasonal += 0.15 if month in [6,7,8] else 0.0

        weekend_factor = 0.88 if dow >= 5 else 1.0
        trend = 1 + 0.0007 * (d - dates[0]).days
        spike = 1.0
        if rng.random() < 0.025:
            spike = rng.uniform(1.4, 2.2)

        lam = max(1, base_demand * seasonal * weekend_factor * trend * spike)
        units_sold = int(rng.poisson(lam))

        received = 0
        # Replenish when inventory is getting low.
        if stock <= base_demand * (lead + 2):
            received = int(base_demand * (lead + 5) * rng.uniform(0.95, 1.15))

        opening = stock
        stock = max(0, stock + received - units_sold)
        stockout = int(opening + received < units_sold)

        rows.append([
            d, mid, name, category, price, lead, opening,
            units_sold, received, stock, stockout
        ])

df = pd.DataFrame(rows, columns=[
    "date","medicine_id","medicine_name","category","unit_price",
    "lead_time_days","opening_stock","units_sold","received_qty",
    "closing_stock","stockout"
])

# Historical demand features
df = df.sort_values(["medicine_id","date"])
g = df.groupby("medicine_id", group_keys=False)
df["lag_1"] = g["units_sold"].shift(1)
df["lag_7"] = g["units_sold"].shift(7)
df["rolling_7"] = g["units_sold"].transform(lambda x: x.shift(1).rolling(7).mean())
df["rolling_14"] = g["units_sold"].transform(lambda x: x.shift(1).rolling(14).mean())
df["rolling_30"] = g["units_sold"].transform(lambda x: x.shift(1).rolling(30).mean())
df["demand_std"] = g["units_sold"].transform(lambda x: x.shift(1).rolling(14).std())
df["month"] = df["date"].dt.month
df["day_of_week"] = df["date"].dt.dayofweek
df["holiday"] = ((df["date"].dt.month == 1) & (df["date"].dt.day == 26)).astype(int)
df["supplier_delay_rate"] = 0.08 + rng.random(len(df))*0.12

# Label: whether the medicine is likely to stock out within the next 7 days.
future_7 = []
for _, grp in df.groupby("medicine_id"):
    future_demand = grp["units_sold"].shift(-1).rolling(7, min_periods=1).sum()
    future_7.append(future_demand)
df["future_7d_demand"] = pd.concat(future_7).sort_index()
df["stockout_risk"] = (
    df["closing_stock"] < df["future_7d_demand"] + df["demand_std"].fillna(0) * 0.5
).astype(int)

df = df.dropna().reset_index(drop=True)
df.to_csv(OUT, index=False)
print(f"Created {OUT} with {len(df):,} rows.")
