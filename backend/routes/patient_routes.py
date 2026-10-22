from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from extensions import db
from models.user import User, Patient
from models.doctor import Doctor, Department
from models.appointment import Appointment
from services import queue_service
from utils.decorators import role_required
from utils.validators import require_fields

patient_bp = Blueprint("patient", __name__, url_prefix="/api/patient")


def _get_patient_or_404():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.patient_profile:
        return None
    return user.patient_profile


@patient_bp.route("/departments", methods=["GET"])
@jwt_required()
def list_departments():
    departments = Department.query.all()
    return jsonify([d.to_dict() for d in departments]), 200


@patient_bp.route("/doctors", methods=["GET"])
@jwt_required()
def list_doctors():
    department_id = request.args.get("department_id", type=int)
    query = Doctor.query
    if department_id:
        query = query.filter_by(department_id=department_id)
    doctors = query.all()
    return jsonify([d.to_dict() for d in doctors]), 200


@patient_bp.route("/doctors/<int:doctor_id>", methods=["GET"])
@jwt_required()
def get_doctor(doctor_id):
    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404
    return jsonify(doctor.to_dict()), 200


@patient_bp.route("/appointments", methods=["POST"])
@role_required("patient")
def book_appointment():
    patient = _get_patient_or_404()
    if not patient:
        return jsonify({"error": "Patient profile not found"}), 404

    data = request.get_json(silent=True) or {}
    missing = require_fields(data, ["doctor_id"])
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    doctor = Doctor.query.get(data["doctor_id"])
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    appointment_type = data.get("appointment_type", "general")
    if appointment_type not in ("general", "follow_up", "emergency"):
        return jsonify({"error": "Invalid appointment_type"}), 400

    try:
        requested_priority = int(data.get("priority_level", 1))
    except (TypeError, ValueError):
        return jsonify({"error": "priority_level must be a number between 1 and 3"}), 400
    priority_level = 3 if appointment_type == "emergency" else requested_priority
    priority_level = max(1, min(priority_level, 3))

    appointment = queue_service.create_appointment_with_prediction(
        patient_id=patient.id,
        doctor=doctor,
        appointment_type=appointment_type,
        priority_level=priority_level,
    )
    position, ahead = queue_service.get_queue_position(appointment)

    result = appointment.to_dict()
    result["queue_position"] = position
    result["patients_ahead"] = ahead
    return jsonify(result), 201


@patient_bp.route("/appointments", methods=["GET"])
@role_required("patient")
def list_my_appointments():
    patient = _get_patient_or_404()
    if not patient:
        return jsonify({"error": "Patient profile not found"}), 404

    status = request.args.get("status")
    query = Appointment.query.filter_by(patient_id=patient.id)
    if status:
        query = query.filter_by(status=status)
    appointments = query.order_by(Appointment.created_at.desc()).all()
    return jsonify([a.to_dict() for a in appointments]), 200


@patient_bp.route("/appointments/<int:appointment_id>/queue-status", methods=["GET"])
@role_required("patient")
def queue_status(appointment_id):
    patient = _get_patient_or_404()
    if not patient:
        return jsonify({"error": "Patient profile not found"}), 404
    appointment = Appointment.query.get(appointment_id)
    if not appointment or appointment.patient_id != patient.id:
        return jsonify({"error": "Appointment not found"}), 404

    position, ahead = queue_service.get_queue_position(appointment)
    result = appointment.to_dict()
    result["queue_position"] = position
    result["patients_ahead"] = ahead
    return jsonify(result), 200


@patient_bp.route("/appointments/<int:appointment_id>/cancel", methods=["POST"])
@role_required("patient")
def cancel_appointment(appointment_id):
    patient = _get_patient_or_404()
    if not patient:
        return jsonify({"error": "Patient profile not found"}), 404
    appointment = Appointment.query.get(appointment_id)
    if not appointment or appointment.patient_id != patient.id:
        return jsonify({"error": "Appointment not found"}), 404
    if appointment.status not in ("waiting",):
        return jsonify({"error": f"Cannot cancel an appointment with status '{appointment.status}'"}), 400

    queue_service.cancel_appointment(appointment)
    return jsonify(appointment.to_dict()), 200


@patient_bp.route("/profile", methods=["GET"])
@role_required("patient")
def get_profile():
    patient = _get_patient_or_404()
    if not patient:
        return jsonify({"error": "Patient profile not found"}), 404
    return jsonify(patient.to_dict()), 200


@patient_bp.route("/profile", methods=["PUT"])
@role_required("patient")
def update_profile():
    patient = _get_patient_or_404()
    if not patient:
        return jsonify({"error": "Patient profile not found"}), 404

    data = request.get_json(silent=True) or {}
    if "full_name" in data:
        patient.user.full_name = data["full_name"]
    if "phone" in data:
        patient.user.phone = data["phone"]
    if "address" in data:
        patient.address = data["address"]
    if "blood_group" in data:
        patient.blood_group = data["blood_group"]
    if "gender" in data:
        gender = (data["gender"] or "").strip().lower() or None
        if gender not in (None, "male", "female", "other"):
            return jsonify({"error": "Invalid gender value"}), 400
        patient.gender = gender

    db.session.commit()
    return jsonify(patient.to_dict()), 200
