# Medicine Stock-Out Prediction & Intelligent Inventory Management

## What this project does
- Generates a realistic synthetic pharmacy inventory dataset.
- Forecasts next-day medicine demand using Random Forest Regression.
- Predicts stock-out risk using Random Forest Classification.
- Forecasts the next 7 days recursively.
- Estimates stock-out ETA.
- Calculates safety stock, reorder point and suggested reorder quantity.
- Provides an interactive Streamlit dashboard.
- Shows simple explanations for risk.

## 1. Install Python
Recommended: Python 3.10–3.12.

## 2. Open terminal in this folder

### Windows
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3. Generate dataset
```bash
python generate_data.py
```

## 4. Train models
```bash
python train_models.py
```

## 5. Run dashboard
```bash
streamlit run app.py
```

The browser should open the local dashboard.

## Project flow
Data → preprocessing → feature engineering → demand forecasting → stock-out classification → risk scoring → reorder decision → dashboard.

## Important academic note
The included dataset is synthetic and intended for a working academic prototype. Do not present synthetic evaluation numbers as results from a real pharmacy. For a research paper, evaluate the final model on an appropriate real/public dataset and report the exact dataset, split and metrics.
