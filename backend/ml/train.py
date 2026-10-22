"""
Trains a Random Forest Regressor on the hospital queue dataset to predict
waiting_time_minutes, evaluates it, and saves the trained model to model.pkl.

Run:
    python train.py

Requires dataset.csv to exist in the same folder (run generate_dataset.py first
if it doesn't, or the training script will generate it automatically).
"""

import os
import json

import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "dataset.csv")
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")
METRICS_PATH = os.path.join(BASE_DIR, "metrics.json")

FEATURE_COLUMNS = [
    "patients_ahead",
    "average_consultation_time",
    "doctor_available",
    "appointment_type",
    "priority_level",
    "day_of_week",
    "hour",
    "doctor_current_load",
    "historical_average_wait",
]
TARGET_COLUMN = "waiting_time_minutes"


def load_dataset():
    if not os.path.exists(DATASET_PATH):
        print("dataset.csv not found - generating synthetic dataset...")
        from generate_dataset import generate_dataset

        df = generate_dataset()
        df.to_csv(DATASET_PATH, index=False)
    else:
        df = pd.read_csv(DATASET_PATH)
    return df


def train():
    df = load_dataset()
    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Small grid search to pick reasonable hyperparameters
    param_grid = {
        "n_estimators": [150, 250],
        "max_depth": [8, 12, None],
        "min_samples_leaf": [1, 2, 4],
    }
    base_model = RandomForestRegressor(random_state=42, n_jobs=-1)
    search = GridSearchCV(
        base_model, param_grid, cv=3, scoring="neg_mean_absolute_error", n_jobs=-1
    )
    search.fit(X_train, y_train)
    model = search.best_estimator_

    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    metrics = {
        "model": "RandomForestRegressor",
        "best_params": search.best_params_,
        "mae_minutes": round(float(mae), 3),
        "rmse_minutes": round(float(rmse), 3),
        "r2_score": round(float(r2), 4),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "feature_columns": FEATURE_COLUMNS,
    }

    print("Training complete. Evaluation metrics:")
    print(json.dumps(metrics, indent=2))

    # Feature importance
    importances = dict(zip(FEATURE_COLUMNS, model.feature_importances_.round(4).tolist()))
    print("\nFeature importances:")
    for k, v in sorted(importances.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")
    metrics["feature_importances"] = importances

    joblib.dump({"model": model, "feature_columns": FEATURE_COLUMNS}, MODEL_PATH)
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\nModel saved to {MODEL_PATH}")
    print(f"Metrics saved to {METRICS_PATH}")
    return metrics


if __name__ == "__main__":
    train()
