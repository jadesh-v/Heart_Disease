"""
main.py – FastAPI backend for Heart Disease Prediction with SHAP explainability.

Run:
    uvicorn main:app --host 127.0.0.1 --port 8000 --reload
"""

import os
import pickle
import logging
from typing import List

import numpy as np
import shap
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Load model artefacts ──────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DL_MODEL_PATH = os.path.join(BASE_DIR, "heart_dl_model.keras")
DL_PREPROCESSING_PATH = os.path.join(BASE_DIR, "dl_preprocessing.pkl")
MODEL_PATH = os.path.join(BASE_DIR, "heart_model.pkl")
MODEL_KIND = "random_forest"

try:
    if os.path.exists(DL_MODEL_PATH) and os.path.exists(DL_PREPROCESSING_PATH):
        import tensorflow as tf

        model = tf.keras.models.load_model(DL_MODEL_PATH)
        with open(DL_PREPROCESSING_PATH, "rb") as f:
            artefacts = pickle.load(f)
        scaler = artefacts["scaler"]
        FEATURE_NAMES = artefacts["feature_names"]
        THRESHOLD = artefacts.get("threshold", 0.5)
        SHAP_BACKGROUND = np.asarray(artefacts.get("background", []), dtype=float)
        MODEL_KIND = "deep_learning"
    else:
        with open(MODEL_PATH, "rb") as f:
            artefacts = pickle.load(f)
        model = artefacts["model"]
        scaler = artefacts["scaler"]
        FEATURE_NAMES = artefacts["feature_names"]
        THRESHOLD = artefacts.get("threshold", 0.5)
        SHAP_BACKGROUND = np.empty((0, len(FEATURE_NAMES)))
    logger.info(
        "%s model loaded. Features: %s | Threshold: %.2f",
        MODEL_KIND,
        FEATURE_NAMES,
        THRESHOLD,
    )
except FileNotFoundError:
    logger.error(
        "heart_model.pkl not found. Run `python train_model.py` first."
    )
    raise RuntimeError("Model file not found. Run train_model.py first.")
except Exception as exc:
    logger.exception("Failed to load model: %s", exc)
    raise

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Heart Disease XAI API",
    description="Predicts heart disease using Deep Learning or Random Forest + SHAP explanations",
    version="1.0.0",
)

import re as _re

# Allowed origins: localhost (dev) + any Vercel deployment (prod)
_ALLOWED_ORIGIN_RE = _re.compile(
    r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
    r"|^https://[a-z0-9\-]+\.vercel\.app$"
    r"|^https://[a-z0-9\-]+\.onrender\.com$"
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$|^https://[a-z0-9\-]+\.vercel\.app$|^https://[a-z0-9\-]+\.onrender\.com$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from auth import router as auth_router
app.include_router(auth_router)

# ── Request / Response schemas ────────────────────────────────────────────────

class PredictRequest(BaseModel):
    age: float = Field(..., ge=1, le=120, description="Age in years")
    sex: float = Field(..., ge=0, le=1, description="Sex (0=Female, 1=Male)")
    cp: float = Field(..., ge=0, le=3, description="Chest pain type (0-3)")
    trestbps: float = Field(..., ge=80, le=220, description="Resting blood pressure (mmHg)")
    chol: float = Field(..., ge=100, le=600, description="Serum cholesterol (mg/dl)")
    fbs: float = Field(..., ge=0, le=1, description="Fasting blood sugar > 120 mg/dl (0/1)")
    restecg: float = Field(..., ge=0, le=2, description="Resting ECG results (0-2)")
    thalach: float = Field(..., ge=60, le=220, description="Max heart rate achieved")
    exang: float = Field(..., ge=0, le=1, description="Exercise induced angina (0/1)")
    oldpeak: float = Field(..., ge=0.0, le=10.0, description="ST depression induced by exercise")
    slope: float = Field(..., ge=0, le=2, description="Slope of peak exercise ST segment (0-2)")
    ca: float = Field(..., ge=0, le=4, description="Number of major vessels colored (0-4)")
    thal: float = Field(..., ge=0, le=3, description="Thalassemia (0-3)")

    model_config = {"strict": False}


class SHAPFeature(BaseModel):
    feature: str
    value: float
    shap_value: float
    direction: str  # "increases" | "decreases"


class PredictResponse(BaseModel):
    prediction: int
    probability: float
    risk_level: str
    shap_values: List[SHAPFeature]
    top_features: List[str]


# ── Helper ────────────────────────────────────────────────────────────────────

def build_input_array(req: PredictRequest) -> np.ndarray:
    """Convert request to a numpy array in the correct feature order."""
    row = [getattr(req, f) for f in FEATURE_NAMES]
    return np.array(row, dtype=float).reshape(1, -1)


def compute_shap(input_scaled: np.ndarray) -> np.ndarray:
    """
    Compute SHAP values for the positive class (heart disease = 1).
    Supports CalibratedClassifierCV wrapping GradientBoostingClassifier.
    Averages SHAP values across the calibration folds.
    Falls back to KernelExplainer if tree-based approach fails.
    """
    if MODEL_KIND == "deep_learning":
        background = SHAP_BACKGROUND
        if background.size == 0:
            background = input_scaled

        def predict_probability(values: np.ndarray) -> np.ndarray:
            return model.predict(values, verbose=0).ravel()

        try:
            explainer = shap.Explainer(predict_probability, background)
            explanation = explainer(input_scaled)
            return np.asarray(explanation.values[0], dtype=float)
        except Exception:
            logger.warning("Neural-network SHAP explainer failed; using KernelExplainer")
            explainer = shap.KernelExplainer(predict_probability, background[:10])
            values = explainer.shap_values(input_scaled, nsamples=200)
            return np.asarray(values[0] if np.asarray(values).ndim > 1 else values, dtype=float)

    from sklearn.calibration import CalibratedClassifierCV as CCCV

    try:
        if isinstance(model, CCCV):
            # CalibratedClassifierCV stores one fitted estimator per fold
            all_sv = []
            for calibrated in model.calibrated_classifiers_:
                base = calibrated.estimator  # the GradientBoostingClassifier
                explainer = shap.TreeExplainer(base)
                raw = explainer.shap_values(input_scaled)
                if isinstance(raw, list):
                    sv = raw[1][0]
                elif raw.ndim == 3:
                    sv = raw[0, :, 1]
                else:
                    sv = raw[0] if raw.ndim == 2 else raw.flatten()
                all_sv.append(sv)
            return np.mean(all_sv, axis=0)  # average across folds

        else:
            # Plain tree model
            explainer = shap.TreeExplainer(model)
            raw = explainer.shap_values(input_scaled)
            if isinstance(raw, list):
                return raw[1][0]
            elif raw.ndim == 3:
                return raw[0, :, 1]
            elif raw.ndim == 2:
                return raw[0]
            else:
                return raw.flatten()

    except Exception:
        # Fallback: model-agnostic KernelExplainer (slower but always works)
        logger.warning("TreeExplainer failed, falling back to KernelExplainer")
        background = input_scaled  # single sample, small background
        explainer = shap.KernelExplainer(
            lambda x: model.predict_proba(x)[:, 1], background
        )
        sv = explainer.shap_values(input_scaled, nsamples=200, silent=True)
        return sv[0] if hasattr(sv, "__len__") and len(sv) > 0 else sv.flatten()



# ── Endpoint ──────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def health():
    return {"status": "ok", "message": "Heart Disease XAI API is running."}


@app.post("/predict", response_model=PredictResponse, tags=["Prediction"])
def predict(req: PredictRequest):
    """
    Accepts 13 clinical parameters, returns prediction, probability,
    risk level, and SHAP-based feature contributions.
    """
    try:
        # 1. Build input array
        X_raw = build_input_array(req)

        # 2. Scale
        X_scaled = scaler.transform(X_raw)

        # 3. Predict probability and apply calibrated threshold
        if MODEL_KIND == "deep_learning":
            proba = float(model.predict(X_scaled, verbose=0).ravel()[0])
        else:
            proba = float(model.predict_proba(X_scaled)[0][1])
        prediction = int(proba >= THRESHOLD)
        prob_pct = round(proba * 100, 2)

        # 4. Risk level
        if proba >= 0.65:
            risk_level = "High Risk"
        elif proba >= 0.35:
            risk_level = "Moderate Risk"
        else:
            risk_level = "Low Risk"

        # 5. SHAP (runs only after prediction)
        sv = compute_shap(X_scaled)

        # 6. Build SHAP features list
        raw_values = X_raw[0]
        shap_features: List[SHAPFeature] = []
        for i, fname in enumerate(FEATURE_NAMES):
            shap_val = float(sv[i])
            direction = "increases" if shap_val > 0 else "decreases"
            shap_features.append(
                SHAPFeature(
                    feature=fname,
                    value=float(raw_values[i]),
                    shap_value=round(shap_val, 6),
                    direction=direction,
                )
            )

        # 7. Top 5 features by |SHAP value|
        sorted_features = sorted(
            shap_features, key=lambda x: abs(x.shap_value), reverse=True
        )
        top_5 = [f.feature for f in sorted_features[:5]]

        logger.info(
            "Prediction=%d | Probability=%.4f | RiskLevel=%s",
            prediction, proba, risk_level,
        )

        return PredictResponse(
            prediction=prediction,
            probability=round(proba * 100, 2),
            risk_level=risk_level,
            shap_values=shap_features,
            top_features=top_5,
        )

    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except Exception as exc:
        logger.exception("Prediction error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(exc)}")
