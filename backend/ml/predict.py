"""
Loads the trained Random Forest model and exposes predict_waiting_time().
Falls back to a simple heuristic if the model file is missing OR cannot be
loaded (e.g. scikit-learn version mismatch with the pickle), so the API never
hard-crashes. Run `python train.py` inside backend/ml to rebuild model.pkl for
your installed scikit-learn version.
"""

import logging
import os

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")

_model_bundle = None
_load_attempted = False


def _load_model():
    global _model_bundle, _load_attempted
    if _model_bundle is None and not _load_attempted:
        _load_attempted = True
        if os.path.exists(MODEL_PATH):
            try:
                _model_bundle = joblib.load(MODEL_PATH)
            except Exception as exc:  # corrupt file / incompatible scikit-learn
                logger.warning(
                    "Could not load %s (%s). Using heuristic fallback - "
                    "run `python train.py` in backend/ml to retrain.",
                    MODEL_PATH,
                    exc,
                )
                _model_bundle = None
    return _model_bundle


def _heuristic_fallback(features: dict) -> float:
    """Used only if model.pkl is missing or cannot be loaded."""
    base = features["patients_ahead"] * features["average_consultation_time"] * 0.9
    load_penalty = features["doctor_current_load"] * 1.3
    unavailable_penalty = 45 if features["doctor_available"] == 0 else 0
    history_blend = features["historical_average_wait"] * 0.35
    priority_discount = {3: -0.85, 2: -0.35, 1: 0.0}.get(features["priority_level"], 0.0)
    value = (base + load_penalty + unavailable_penalty + history_blend) * (1 + priority_discount)
    return float(np.clip(value, 2, 240))


def predict_waiting_time(features: dict) -> float:
    """
    features must contain:
        patients_ahead, average_consultation_time, doctor_available,
        appointment_type, priority_level, day_of_week, hour,
        doctor_current_load, historical_average_wait
    Returns predicted waiting time in minutes (float, rounded to 1 decimal).
    """
    bundle = _load_model()
    if bundle is None:
        return round(_heuristic_fallback(features), 1)

    try:
        model = bundle["model"]
        columns = bundle["feature_columns"]
        # DataFrame keeps the feature names the model was trained with
        row = pd.DataFrame([[features[col] for col in columns]], columns=columns)
        prediction = model.predict(row)[0]
        return round(float(np.clip(prediction, 1, 300)), 1)
    except Exception as exc:
        logger.warning("Model prediction failed (%s). Using heuristic fallback.", exc)
        return round(_heuristic_fallback(features), 1)


def model_is_trained() -> bool:
    return _load_model() is not None
