import pandas as pd
import joblib
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import mean_absolute_error, mean_squared_error, accuracy_score, f1_score, roc_auc_score

DATA = Path("data/medicine_sales.csv")
MODEL_DIR = Path("models")
MODEL_DIR.mkdir(exist_ok=True)

df = pd.read_csv(DATA, parse_dates=["date"])
df = df.sort_values(["date","medicine_id"]).reset_index(drop=True)

demand_features = [
    "lag_1","lag_7","rolling_7","rolling_14","rolling_30",
    "month","day_of_week","holiday","closing_stock","lead_time_days"
]

risk_features = [
    "closing_stock","rolling_7","rolling_14","rolling_30",
    "lead_time_days","demand_std","supplier_delay_rate"
]

# Chronological split: never randomly mix future data into training.
cutoff = df["date"].quantile(0.80)
train = df[df["date"] <= cutoff].copy()
test = df[df["date"] > cutoff].copy()

reg = RandomForestRegressor(
    n_estimators=250, max_depth=14, min_samples_leaf=2,
    random_state=42, n_jobs=-1
)
reg.fit(train[demand_features], train["units_sold"])
pred = reg.predict(test[demand_features])

mae = mean_absolute_error(test["units_sold"], pred)
rmse = mean_squared_error(test["units_sold"], pred) ** 0.5

clf = RandomForestClassifier(
    n_estimators=250, max_depth=12, min_samples_leaf=2,
    class_weight="balanced", random_state=42, n_jobs=-1
)
clf.fit(train[risk_features], train["stockout_risk"])
risk_pred = clf.predict(test[risk_features])
risk_prob = clf.predict_proba(test[risk_features])[:,1]

acc = accuracy_score(test["stockout_risk"], risk_pred)
f1 = f1_score(test["stockout_risk"], risk_pred, zero_division=0)
try:
    auc = roc_auc_score(test["stockout_risk"], risk_prob)
except ValueError:
    auc = float("nan")

joblib.dump(reg, MODEL_DIR / "demand_model.pkl")
joblib.dump(clf, MODEL_DIR / "stockout_model.pkl")

metrics = {
    "demand_MAE": float(mae),
    "demand_RMSE": float(rmse),
    "risk_accuracy": float(acc),
    "risk_F1": float(f1),
    "risk_ROC_AUC": None if pd.isna(auc) else float(auc)
}
pd.Series(metrics).to_json(MODEL_DIR / "metrics.json", indent=2)

print("Models trained successfully.")
print(f"Demand MAE: {mae:.2f}")
print(f"Demand RMSE: {rmse:.2f}")
print(f"Risk Accuracy: {acc:.3f}")
print(f"Risk F1: {f1:.3f}")
print(f"Risk ROC-AUC: {auc:.3f}")
