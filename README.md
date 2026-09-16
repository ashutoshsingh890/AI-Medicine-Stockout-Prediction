# 💊 Medicine Stock-Out Prediction & Intelligent Inventory Management

An AI/ML-based pharmacy inventory management system that predicts medicine demand, identifies stock-out risk, and supports intelligent inventory decisions through an interactive Streamlit dashboard.

## 🚀 Live Demo

🔗 https://med-stock-predictor--ashutoshsing336.replit.app

## 📌 Project Overview

Medicine stock-outs can affect the availability of essential medicines and make inventory planning difficult.

This project combines **Machine Learning, Inventory Management, and Data Analytics** to provide a prototype system for:

- Medicine demand forecasting
- Stock-out risk prediction
- 7-day demand forecasting
- Stock-out ETA estimation
- Reorder point calculation
- Safety stock calculation
- Suggested reorder quantity
- Medicine and supplier management
- Inventory transaction tracking
- Expiry-risk monitoring
- What-if inventory simulation
- Automated inventory alerts
- Interactive dashboard

> **Academic Note:** The dataset used in this project is synthetic and generated for an academic prototype. The reported ML metrics should not be interpreted as real-world pharmacy performance.

---

## ✨ Key Features

### 🤖 Machine Learning

- Random Forest Regression for medicine demand forecasting
- Random Forest Classification for stock-out risk prediction
- Recursive 7-day demand forecasting
- Stock-out risk scoring
- Simple risk explanations

### 📦 Inventory Management

- Stock-in and sales transactions
- Current stock calculation
- Low-stock detection
- Inventory transaction history
- Negative-stock prevention

### 🔄 Intelligent Reordering

The system calculates:

- Lead-time demand
- Safety stock
- Reorder point
- Recommended reorder quantity
- Reorder decision

### ⏰ Expiry Risk Management

Medicines can be monitored based on expiry date:

- Expired
- Critical
- Warning
- Safe
- No expiry information

### 📊 What-If Simulation

Users can simulate changes in medicine demand and observe:

- Adjusted demand
- Estimated days until stock-out
- Remaining inventory

### 🚨 Alert Center

The dashboard can identify important inventory conditions such as:

- Low stock
- Stock-out risk
- Expiry risk
- Reorder requirements

### 👥 User Authentication

Role-based access is included for:

- Admin
- Pharmacy Staff

---

## 🧠 Machine Learning Results

The models were trained and evaluated on the generated synthetic dataset.

| Metric | Result |
|---|---:|
| Demand Forecast MAE | 11.88 |
| Demand Forecast RMSE | 19.68 |
| Stock-Out Accuracy | 95.5% |
| Stock-Out F1 Score | 93.9% |
| Stock-Out ROC-AUC | 0.993 |

**Dataset:** 6,700 synthetic records.

These results demonstrate the behavior of the prototype on its generated dataset and are not evidence of performance in a real pharmacy environment.

---

## 🛠️ Technology Stack

### Programming
- Python

### Data & Machine Learning
- Pandas
- NumPy
- Scikit-learn
- Joblib

### Application
- Streamlit

### Database
- SQLite

### Security
- Bcrypt password hashing

### Development
- VS Code
- Git
- GitHub

---

## 🔄 Project Workflow

```text
Synthetic Data Generation
          ↓
Data Preprocessing
          ↓
Feature Engineering
          ↓
Demand Forecasting
          ↓
Stock-Out Risk Classification
          ↓
Risk Analysis
          ↓
Inventory Monitoring
          ↓
Reorder Recommendation
          ↓
Expiry & Alert Management
          ↓
Streamlit Dashboard