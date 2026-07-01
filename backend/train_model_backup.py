"""
train_model.py
Trains a HistGradientBoosting classifier on the UCI Heart Disease dataset.
Applies clinical monotonic constraints based on domain knowledge:
  - Higher age → more risk
  - Male (sex=1) → more risk
  - Higher resting BP → more risk
  - Higher cholesterol → more risk
  - Higher fasting blood sugar → more risk
  - Lower max heart rate → more risk  (constraint = -1)
  - Exercise-induced angina (1) → more risk
  - Higher ST depression (oldpeak) → more risk
  - More major vessels (ca) → more risk
  - Reversible thal defect → more risk
  Features cp, restecg, slope are left unconstrained because
  their pattern in this dataset is non-monotonic.
"""

import pandas as pd
import numpy as np
import pickle
import os
import warnings
warnings.filterwarnings("ignore")

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score

# ── Feature/Target configuration ──────────────────────────────────────────────
TARGET_COL = "target"

COLUMN_RENAME = {
    "age": "age",
    "sex": "sex",
    "chest_pain_type": "cp",
    "resting_blood_pressure": "trestbps",
    "cholestoral": "chol",
    "fasting_blood_sugar": "fbs",
    "rest_ecg": "restecg",
    "Max_heart_rate": "thalach",
    "exercise_induced_angina": "exang",
    "oldpeak": "oldpeak",
    "slope": "slope",
    "vessels_colored_by_flourosopy": "ca",
    "thalassemia": "thal",
    "target": "target",
}

FEATURE_ORDER = [
    "age", "sex", "cp", "trestbps", "chol",
    "fbs", "restecg", "thalach", "exang",
    "oldpeak", "slope", "ca", "thal",
]

# ── Clinical monotonic constraints ─────────────────────────────────────────────
# +1 = feature increasing → risk increases
# -1 = feature increasing → risk decreases
#  0 = no constraint (non-monotonic in this dataset)
# Order matches FEATURE_ORDER exactly.
MONOTONIC_CST = [
     1,   # age:      older → more risk
     1,   # sex:      male(1) → more risk
     0,   # cp:       non-monotonic in dataset (typical angina=0 has highest disease rate)
     1,   # trestbps: higher BP → more risk
     1,   # chol:     higher cholesterol → more risk
     1,   # fbs:      high blood sugar → more risk
     0,   # restecg:  non-monotonic (values 0,1,2 don't follow linear risk order)
    -1,   # thalach:  lower max heart rate → more risk
     1,   # exang:    exercise angina(1) → more risk
     1,   # oldpeak:  higher ST depression → more risk
     1,   # slope:    flat/downsloping segment → more risk (now constrained!)
     1,   # ca:       more vessels colored → more risk
     1,   # thal:     higher value (defect) → more risk
]

# ── Categorical encoders ───────────────────────────────────────────────────────
SEX_MAP     = {"Male": 1, "Female": 0}
CP_MAP      = {"Asymptomatic": 0, "Non-anginal pain": 1, "Atypical angina": 2, "Typical angina": 3}
FBS_MAP     = {"Greater than 120 mg/ml": 1, "Lower than 120 mg/ml": 0}
RESTECG_MAP = {"Normal": 0, "ST-T wave abnormality": 1, "Left ventricular hypertrophy": 2}
EXANG_MAP   = {"Yes": 1, "No": 0}
SLOPE_MAP   = {"Downsloping": 0, "Flat": 1, "Upsloping": 2}
CA_MAP      = {"Zero": 0, "One": 1, "Two": 2, "Three": 3, "Four": 4, 0: 0, 1: 1, 2: 2, 3: 3, 4: 4}
THAL_MAP    = {"Fixed Defect": 0, "Normal": 1, "Reversable Defect": 2, "No": 3}

TARGET_MAP  = {"Presence": 1, "Absence": 0, 1: 1, 0: 0}


def encode(df: pd.DataFrame) -> pd.DataFrame:
    df["sex"]     = df["sex"].map(SEX_MAP).fillna(df["sex"])
    df["cp"]      = df["cp"].map(CP_MAP).fillna(df["cp"])
    df["fbs"]     = df["fbs"].map(FBS_MAP).fillna(df["fbs"])
    df["restecg"] = df["restecg"].map(RESTECG_MAP).fillna(df["restecg"])
    df["exang"]   = df["exang"].map(EXANG_MAP).fillna(df["exang"])
    df["slope"]   = df["slope"].map(SLOPE_MAP).fillna(df["slope"])
    df["ca"]      = df["ca"].map(CA_MAP).fillna(df["ca"])
    df["thal"]    = df["thal"].map(THAL_MAP).fillna(df["thal"])
    df["target"]  = df["target"].map(TARGET_MAP).fillna(df["target"])
    return df


def train():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "heart.csv")

    print(f"[INFO] Loading dataset: {csv_path}")
    df = pd.read_csv(csv_path)

    # Rename to canonical names
    df = df.rename(columns=COLUMN_RENAME)
    df = df.dropna(subset=[TARGET_COL])

    # Encode categoricals
    df = encode(df)

    # Keep only required columns, convert to numeric, drop NaN
    df = df[FEATURE_ORDER + [TARGET_COL]]
    df = df.apply(pd.to_numeric, errors="coerce").dropna()

    print(f"[INFO] Raw shape: {df.shape} | Duplicates: {df.duplicated().sum()}")

    # ── CRITICAL FIX: Remove duplicate rows ────────────────────────────────────
    df = df.drop_duplicates()
    print(f"[INFO] After deduplication: {df.shape}")

    X = df[FEATURE_ORDER].values
    y = df[TARGET_COL].values.astype(int)

    # ── CRITICAL: this dataset uses 1=No Disease, 0=Disease (inverted from UCI)
    # Flip so that 1 = Heart Disease (positive class), 0 = No Disease
    y = 1 - y

    print(f"[INFO] Class distribution | No Disease (0): {(y==0).sum()} | Disease (1): {(y==1).sum()}")

    # Train/test split — stratified
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Scale
    scaler = StandardScaler()
    X_train_sc = scaler.fit_transform(X_train)
    X_test_sc  = scaler.transform(X_test)

    # ── HistGradientBoosting with clinical monotonic constraints ───────────────
    print("[INFO] Training with clinical monotonic constraints:")
    for feat, cst in zip(FEATURE_ORDER, MONOTONIC_CST):
        direction = "+risk" if cst == 1 else "-risk" if cst == -1 else "unconstrained"
        print(f"        {feat:<12}: {direction}")

    model = HistGradientBoostingClassifier(
        max_iter=500,
        learning_rate=0.03,
        max_depth=4,
        min_samples_leaf=15,
        l2_regularization=0.5,
        monotonic_cst=MONOTONIC_CST,
        random_state=42,
        class_weight={0: 1.0, 1: 1.3},   # mild upweight for disease class
    )

    # ── 5-fold cross-validation ────────────────────────────────────────────────
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, X_train_sc, y_train, cv=cv, scoring="roc_auc")
    print(f"\n[INFO] 5-Fold CV ROC-AUC: {cv_scores.mean():.4f} +/- {cv_scores.std():.4f}")

    # ── Fit model ─────────────────────────────────────────────────────────────
    model.fit(X_train_sc, y_train)

    # ── Find optimal threshold to maximize recall while keeping precision > 60% ─
    from sklearn.metrics import recall_score, f1_score
    proba_train = model.predict_proba(X_train_sc)[:, 1]
    best_thresh = 0.5
    best_f1 = 0
    for t in np.arange(0.20, 0.65, 0.01):
        preds_t = (proba_train >= t).astype(int)
        rec = recall_score(y_train, preds_t, zero_division=0)
        prec = recall_score(y_train, preds_t, pos_label=0, zero_division=0)  # no-disease recall
        if rec >= 0.78 and prec >= 0.65:  # want high disease recall, decent specificity
            f1 = f1_score(y_train, preds_t)
            if f1 > best_f1:
                best_f1 = f1
                best_thresh = t

    print(f"[INFO] Optimal decision threshold: {best_thresh:.2f}")

    # ── Evaluate on held-out test set (using optimal threshold) ─────────────
    y_proba = model.predict_proba(X_test_sc)[:, 1]
    y_pred  = (y_proba >= best_thresh).astype(int)
    acc     = accuracy_score(y_test, y_pred)
    auc     = roc_auc_score(y_test, y_proba)

    print(f"\n[RESULTS] Test Accuracy : {acc:.4f}")
    print(f"[RESULTS] Test ROC-AUC  : {auc:.4f}")
    print("\n[RESULTS] Classification Report:")
    print(classification_report(y_test, y_pred, target_names=["No Disease", "Disease"]))

    if acc >= 0.99:
        print("[WARNING] Suspiciously high accuracy -- check for remaining duplicates or leakage.")
    elif acc >= 0.78:
        print("[INFO] Accuracy looks realistic for this dataset.")

    # ── Verify clinical directions are respected ───────────────────────────────
    print("\n[VERIFY] Clinical direction check (holding all other features at median):")
    X_median = np.median(X_train, axis=0)
    checks = [
        ("age",      0,  35,  70),
        ("sex",      1,  0,   1),
        ("trestbps", 3,  110, 170),
        ("chol",     4,  180, 320),
        ("thalach",  7,  190, 100),   # low bpm = more risk
        ("exang",    8,  0,   1),
        ("oldpeak",  9,  0.1, 4.5),
        ("slope",    10, 0,   2),
        ("ca",       11, 0,   3),
        ("thal",     12, 0,   2),
    ]
    all_ok = True
    for name, idx, lo, hi in checks:
        r_lo = X_median.copy(); r_lo[idx] = lo
        r_hi = X_median.copy(); r_hi[idx] = hi
        p_lo = model.predict_proba(scaler.transform([r_lo]))[0][1]
        p_hi = model.predict_proba(scaler.transform([r_hi]))[0][1]
        ok = p_hi > p_lo
        if not ok:
            all_ok = False
        print(f"  {name:<12}: low={p_lo*100:.1f}%  high={p_hi*100:.1f}%  {'OK' if ok else 'CONSTRAINT FAILED'}")
    if all_ok:
        print("[INFO] All clinical constraints satisfied.")

    # ── Save ──────────────────────────────────────────────────────────────────
    model_path = os.path.join(base_dir, "heart_model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump({
            "model": model,
            "scaler": scaler,
            "feature_names": FEATURE_ORDER,
            "threshold": best_thresh,
        }, f)

    print(f"\n[SUCCESS] Model saved -> {model_path}")


if __name__ == "__main__":
    train()
