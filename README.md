# 🫀 Explainable AI-Based Heart Disease Prediction System

> **CardioXAI** — A full-stack AI medical dashboard that predicts heart disease from 13 clinical parameters and explains every prediction using SHAP (SHapley Additive exPlanations).

---

## 📋 Project Description

This system applies **Explainable AI (XAI)** to cardiovascular risk assessment. A **Random Forest Classifier** trained on the UCI Heart Disease dataset makes predictions, while **SHAP** reveals _why_ the model made each decision — showing which clinical features drove the risk score up or down.

The platform features:
- A modern **Next.js + React** medical dashboard UI
- A **FastAPI** REST backend with proper error handling
- **SHAP TreeExplainer** for post-hoc, feature-level explanations
- Animated probability ring, SHAP bar charts, and top-5 feature highlights

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, React 19, TypeScript, Vanilla CSS |
| Backend | FastAPI, Uvicorn, Python 3.10+ |
| ML Model | Random Forest Classifier (scikit-learn) |
| Explainability | SHAP (TreeExplainer) |
| Preprocessing | StandardScaler |
| Dataset | `heart.csv` (1,025 rows, 13 features) |

---

## 📂 Project Structure

```
Heart-Disease-XAI/
│
├── backend/
│   ├── main.py              ← FastAPI server with /predict endpoint
│   ├── train_model.py       ← Model training + preprocessing script
│   ├── heart.csv            ← Dataset
│   ├── heart_model.pkl      ← Saved model + scaler (generated)
│   └── requirements.txt     ← Python dependencies
│
├── frontend/
│   ├── app/
│   │   ├── globals.css      ← Design system & global styles
│   │   ├── layout.tsx       ← Root layout + Google Fonts
│   │   └── page.tsx         ← Main dashboard page
│   ├── components/
│   │   ├── types.ts         ← TypeScript interfaces
│   │   ├── PredictionForm.tsx ← 13-field clinical input form
│   │   └── ResultPanel.tsx  ← Results, SHAP table, probability ring
│   ├── next.config.js       ← Next.js configuration
│   └── package.json         ← Node dependencies
│
├── .gitignore
└── README.md
```

---

## ⚙️ Input Features (13 Parameters)

| Feature | Name | Range |
|---|---|---|
| `age` | Age in years | 1–120 |
| `sex` | Sex (0=Female, 1=Male) | 0 or 1 |
| `cp` | Chest Pain Type | 0–3 |
| `trestbps` | Resting Blood Pressure (mmHg) | 80–220 |
| `chol` | Serum Cholesterol (mg/dl) | 100–600 |
| `fbs` | Fasting Blood Sugar > 120 mg/dl | 0 or 1 |
| `restecg` | Resting ECG Results | 0–2 |
| `thalach` | Max Heart Rate Achieved | 60–220 |
| `exang` | Exercise Induced Angina | 0 or 1 |
| `oldpeak` | ST Depression (Exercise vs Rest) | 0.0–10.0 |
| `slope` | Slope of Peak ST Segment | 0–2 |
| `ca` | Major Vessels (Fluoroscopy) | 0–4 |
| `thal` | Thalassemia Status | 0–3 |

---

## 🚀 Setup & Running

### Prerequisites
- Python 3.10+
- Node.js 18+ & npm
- pip

---

### 1️⃣ Backend Setup

```bash
# Navigate to backend
cd Heart-Disease-XAI/backend

# Install dependencies
pip install -r requirements.txt

# Train the model (generates heart_model.pkl)
python train_model.py

# Start the FastAPI server
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Backend will be available at: **http://127.0.0.1:8000**  
API Docs (Swagger UI): **http://127.0.0.1:8000/docs**

---

### 2️⃣ Frontend Setup

```bash
# Navigate to frontend
cd Heart-Disease-XAI/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be available at: **http://localhost:3000**

---

## 📡 API Reference

### `POST /predict`

**Request Body (JSON):**
```json
{
  "age": 52,
  "sex": 1,
  "cp": 0,
  "trestbps": 125,
  "chol": 212,
  "fbs": 0,
  "restecg": 1,
  "thalach": 168,
  "exang": 0,
  "oldpeak": 1.0,
  "slope": 2,
  "ca": 2,
  "thal": 3
}
```

**Response (JSON):**
```json
{
  "prediction": 0,
  "probability": 12.5,
  "risk_level": "Low Risk",
  "shap_values": [
    {
      "feature": "thalach",
      "value": 168,
      "shap_value": -0.0842,
      "direction": "decreases"
    },
    ...
  ],
  "top_features": ["thalach", "ca", "cp", "oldpeak", "thal"]
}
```

**Response Fields:**
| Field | Description |
|---|---|
| `prediction` | 0 = No Disease, 1 = Disease |
| `probability` | Probability of disease (0–100%) |
| `risk_level` | "Low Risk" / "Moderate Risk" / "High Risk" |
| `shap_values` | Per-feature SHAP contribution values |
| `top_features` | Top 5 most influential features |

---

## 🧠 How SHAP Works in This Project

**SHAP (SHapley Additive exPlanations)** is a game-theory-based method for explaining machine learning predictions.

**In this project:**
1. After the Random Forest makes a prediction, `shap.TreeExplainer` is initialized with the trained model.
2. For the given patient's scaled feature vector, SHAP computes a **contribution value** for each of the 13 features.
3. **Positive SHAP values** → the feature *increased* the probability of heart disease.
4. **Negative SHAP values** → the feature *decreased* the probability of heart disease.
5. The magnitude of each value shows how strongly it influenced the outcome.
6. The top 5 features (by |SHAP value|) are highlighted in the dashboard.

**Why it matters:** Unlike traditional "black-box" AI models, SHAP allows clinicians and researchers to understand _what_ drove a specific prediction — a critical requirement in medical AI.

---

## 🔧 Technical Notes

- Dataset: UCI Heart Disease dataset (Cleveland, adapted)
- Model: `RandomForestClassifier` with 200 estimators, max_depth=10
- Preprocessing: `StandardScaler` applied before training and inference
- SHAP: `TreeExplainer` used for exact, efficient explanations on tree-based models
- Feature order is strictly maintained between training and inference to prevent mismatch errors

---

## ⚠️ Disclaimer

> **Note:** This system is intended for informational and research purposes. Predictions should not be used as a substitute for professional medical diagnosis or clinical judgment.
