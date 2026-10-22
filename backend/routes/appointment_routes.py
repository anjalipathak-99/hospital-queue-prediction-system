from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

from models.appointment import Appointment
from models.user import User

appointment_bp = Blueprint("appointment", __name__, url_prefix="/api/appointments")


@appointment_bp.route("/<int:appointment_id>", methods=["GET"])
@jwt_required()
def get_appointment(appointment_id):
    """Shared read endpoint - accessible by the owning patient, the assigned doctor, or an admin."""
    claims = get_jwt()
    user_id = get_jwt_identity()
    role = claims.get("role")

    appointment = Appointment.query.get(appointment_id)
    if not appointment:
        return jsonify({"error": "Appointment not found"}), 404

    if role == "admin":
        return jsonify(appointment.to_dict()), 200

    user = User.query.get(user_id)
    if role == "patient" and user.patient_profile and appointment.patient_id == user.patient_profile.id:
        return jsonify(appointment.to_dict()), 200
    if role == "doctor" and user.doctor_profile and appointment.doctor_id == user.doctor_profile.id:
        return jsonify(appointment.to_dict()), 200

    return jsonify({"error": "Forbidden"}), 403
