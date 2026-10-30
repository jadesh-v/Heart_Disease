"""
Train the CardioXAI neural-network model and compare it with the Random Forest
baseline using the same deduplicated data split.

The test set is kept separate from threshold selection and model selection.
Run from this directory with:

    python train_dl_model.py
"""

import json
import os
import pickle
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from train_model import (
    COLUMN_RENAME,
    FEATURE_ORDER,
    TARGET_COL,
    encode,
)

RANDOM_STATE = 42


def metrics_at_threshold(
    y_true: np.ndarray, probabilities: np.ndarray, threshold: float
) -> dict[str, Any]:
    predictions = (probabilities >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, predictions, labels=[0, 1]).ravel()
    return {
        "accuracy": round(float(accuracy_score(y_true, predictions)), 6),
        "precision": round(float(precision_score(y_true, predictions, zero_division=0)), 6),
        "recall": round(float(recall_score(y_true, predictions, zero_division=0)), 6),
        "f1": round(float(f1_score(y_true, predictions, zero_division=0)), 6),
        "roc_auc": round(float(roc_auc_score(y_true, probabilities)), 6),
        "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
        "threshold": round(float(threshold), 4),
    }


def choose_threshold(y_true: np.ndarray, probabilities: np.ndarray) -> float:
    candidates = np.arange(0.20, 0.66, 0.01)
    eligible = []
    for threshold in candidates:
        metrics = metrics_at_threshold(y_true, probabilities, float(threshold))
        if metrics["recall"] >= 0.78 and metrics["precision"] >= 0.60:
            eligible.append(metrics)
    if not eligible:
        return 0.5
    return float(max(eligible, key=lambda item: item["f1"])["threshold"])


def load_data(base_dir: str) -> tuple[np.ndarray, np.ndarray]:
    frame = pd.read_csv(os.path.join(base_dir, "heart.csv"))
    frame = frame.rename(columns=COLUMN_RENAME).dropna(subset=[TARGET_COL])
    frame = encode(frame)
    frame = frame[FEATURE_ORDER + [TARGET_COL]]
    frame = frame.apply(pd.to_numeric, errors="coerce").dropna().drop_duplicates()
    features = frame[FEATURE_ORDER].to_numpy(dtype=np.float32)
    target = 1 - frame[TARGET_COL].to_numpy(dtype=np.int32)
    return features, target


def build_network() -> tf.keras.Model:
    model = tf.keras.Sequential(
        [
            tf.keras.layers.Input(shape=(len(FEATURE_ORDER),)),
            tf.keras.layers.Dense(64, activation="relu"),
            tf.keras.layers.Dropout(0.25),
            tf.keras.layers.Dense(32, activation="relu"),
            tf.keras.layers.Dropout(0.20),
            tf.keras.layers.Dense(16, activation="relu"),
            tf.keras.layers.Dense(1, activation="sigmoid"),
        ],
        name="cardioxai_mlp",
    )
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss="binary_crossentropy",
        metrics=[
            tf.keras.metrics.BinaryAccuracy(name="accuracy"),
            tf.keras.metrics.Precision(name="precision"),
            tf.keras.metrics.Recall(name="recall"),
            tf.keras.metrics.AUC(name="roc_auc"),
        ],
    )
    return model


def train() -> None:
    tf.keras.utils.set_random_seed(RANDOM_STATE)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    X, y = load_data(base_dir)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )
    X_fit, X_validation, y_fit, y_validation = train_test_split(
        X_train, y_train, test_size=0.2, random_state=RANDOM_STATE, stratify=y_train
    )

    scaler = StandardScaler()
    X_fit_scaled = scaler.fit_transform(X_fit).astype(np.float32)
    X_validation_scaled = scaler.transform(X_validation).astype(np.float32)
    X_test_scaled = scaler.transform(X_test).astype(np.float32)
    X_train_scaled = scaler.transform(X_train).astype(np.float32)

    model = build_network()
    history = model.fit(
        X_fit_scaled,
        y_fit,
        validation_data=(X_validation_scaled, y_validation),
        epochs=200,
        batch_size=32,
        callbacks=[
            tf.keras.callbacks.EarlyStopping(
                monitor="val_loss", patience=20, restore_best_weights=True
            )
        ],
        verbose=1,
    )

    validation_probabilities = model.predict(X_validation_scaled, verbose=0).ravel()
    threshold = choose_threshold(y_validation, validation_probabilities)
    dl_probabilities = model.predict(X_test_scaled, verbose=0).ravel()

    baseline = RandomForestClassifier(
        n_estimators=300,
        max_depth=5,
        min_samples_leaf=5,
        max_features="sqrt",
        random_state=RANDOM_STATE,
        class_weight={0: 1.0, 1: 1.3},
    )
    baseline.fit(X_fit_scaled, y_fit)
    baseline_validation_probabilities = baseline.predict_proba(X_validation_scaled)[:, 1]
    baseline_threshold = choose_threshold(
        y_validation, baseline_validation_probabilities
    )
    baseline.fit(X_train_scaled, y_train)
    baseline_probabilities = baseline.predict_proba(X_test_scaled)[:, 1]

    metrics = {
        "dataset_rows": int(len(X)),
        "feature_names": FEATURE_ORDER,
        "neural_network": metrics_at_threshold(y_test, dl_probabilities, threshold),
        "random_forest_baseline": metrics_at_threshold(
            y_test, baseline_probabilities, baseline_threshold
        ),
    }

    model.save(os.path.join(base_dir, "heart_dl_model.keras"))
    with open(os.path.join(base_dir, "dl_preprocessing.pkl"), "wb") as file:
        pickle.dump(
            {
                "scaler": scaler,
                "feature_names": FEATURE_ORDER,
                "threshold": threshold,
                "background": X_train_scaled[: min(100, len(X_train_scaled))],
            },
            file,
        )
    with open(os.path.join(base_dir, "model_metrics.json"), "w", encoding="utf-8") as file:
        json.dump(metrics, file, indent=2)

    figure, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].plot(history.history["accuracy"], label="Training")
    axes[0].plot(history.history["val_accuracy"], label="Validation")
    axes[0].set_title("Accuracy")
    axes[0].set_xlabel("Epoch")
    axes[0].legend()
    axes[1].plot(history.history["loss"], label="Training")
    axes[1].plot(history.history["val_loss"], label="Validation")
    axes[1].set_title("Loss")
    axes[1].set_xlabel("Epoch")
    axes[1].legend()
    figure.tight_layout()
    figure.savefig(os.path.join(base_dir, "training_history.png"), dpi=150)
    plt.close(figure)

    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    train()
