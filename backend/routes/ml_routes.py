from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from ml.predict import predict_waiting_time, model_is_trained
from utils.validators import require_fields

ml_bp = Blueprint("ml", __name__, url_prefix="/api/ml")

REQUIRED_FEATURES = [
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


@ml_bp.route("/predict", methods=["POST"])
@jwt_required()
def predict():
    """
    Accepts raw queue-state features and returns the predicted waiting time.

    Example request body:
    {
      "patients_ahead": 17,
      "average_consultation_time": 15,
      "doctor_available": 1,
      "appointment_type": 0,
      "priority_level": 1,
      "day_of_week": 2,
      "hour": 11,
      "doctor_current_load": 12,
      "historical_average_wait": 28
    }
    """
    data = request.get_json(silent=True) or {}
    missing = require_fields(data, REQUIRED_FEATURES)
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    try:
        features = {key: float(data[key]) if key not in (
            "patients_ahead", "doctor_available", "appointment_type",
            "priority_level", "day_of_week", "hour", "doctor_current_load",
        ) else int(data[key]) for key in REQUIRED_FEATURES}
    except (TypeError, ValueError):
        return jsonify({"error": "All feature values must be numeric"}), 400

    predicted_minutes = predict_waiting_time(features)

    return jsonify({
        "patients_ahead": features["patients_ahead"],
        "predicted_waiting_time": predicted_minutes,
        "unit": "minutes",
        "model_trained": model_is_trained(),
    }), 200


@ml_bp.route("/status", methods=["GET"])
@jwt_required()
def status():
    return jsonify({"model_trained": model_is_trained()}), 200
