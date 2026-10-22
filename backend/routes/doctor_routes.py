from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity

from extensions import db
from models.user import User
from models.appointment import Appointment
from services import queue_service
from utils.decorators import role_required
from utils.timeutils import today

doctor_bp = Blueprint("doctor", __name__, url_prefix="/api/doctor")


def _get_doctor_or_404():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.doctor_profile:
        return None
    return user.doctor_profile


@doctor_bp.route("/queue", methods=["GET"])
@role_required("doctor")
def today_queue():
    doctor = _get_doctor_or_404()
    if not doctor:
        return jsonify({"error": "Doctor profile not found"}), 404

    appointments = (
        Appointment.query.filter(
            Appointment.doctor_id == doctor.id,
            db.func.date(Appointment.created_at) == today(),
            Appointment.status.in_(["waiting", "consulting"]),
        )
        .order_by(Appointment.priority_level.desc(), Appointment.queue_number.asc())
        .all()
    )
    return jsonify([a.to_dict() for a in appointments]), 200


@doctor_bp.route("/appointments/today", methods=["GET"])
@role_required("doctor")
def todays_appointments():
    doctor = _get_doctor_or_404()
    if not doctor:
        return jsonify({"error": "Doctor profile not found"}), 404

    appointments = (
        Appointment.query.filter(
            Appointment.doctor_id == doctor.id,
            db.func.date(Appointment.created_at) == today(),
        )
        .order_by(Appointment.queue_number.asc())
        .all()
    )
    return jsonify([a.to_dict() for a in appointments]), 200


def _get_own_appointment(doctor, appointment_id):
    appointment = Appointment.query.get(appointment_id)
    if not appointment or appointment.doctor_id != doctor.id:
        return None
    return appointment


@doctor_bp.route("/appointments/<int:appointment_id>/start", methods=["POST"])
@role_required("doctor")
def start_consultation(appointment_id):
    doctor = _get_doctor_or_404()
    if not doctor:
        return jsonify({"error": "Doctor profile not found"}), 404
    appointment = _get_own_appointment(doctor, appointment_id)
    if not appointment:
        return jsonify({"error": "Appointment not found"}), 404
    if appointment.status != "waiting":
        return jsonify({"error": f"Cannot start consultation from status '{appointment.status}'"}), 400

    already_consulting = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.status == "consulting",
        db.func.date(Appointment.created_at) == today(),
    ).first()
    if already_consulting:
        return jsonify({"error": "Complete the current consultation before starting another"}), 409

    queue_service.start_consultation(appointment)
    return jsonify(appointment.to_dict()), 200


@doctor_bp.route("/appointments/<int:appointment_id>/complete", methods=["POST"])
@role_required("doctor")
def complete_consultation(appointment_id):
    doctor = _get_doctor_or_404()
    if not doctor:
        return jsonify({"error": "Doctor profile not found"}), 404
    appointment = _get_own_appointment(doctor, appointment_id)
    if not appointment:
        return jsonify({"error": "Appointment not found"}), 404
    if appointment.status != "consulting":
        return jsonify({"error": f"Cannot complete an appointment with status '{appointment.status}'"}), 400

    data = request.get_json(silent=True) or {}
    queue_service.complete_consultation(appointment, notes=data.get("notes"))
    return jsonify(appointment.to_dict()), 200


@doctor_bp.route("/appointments/<int:appointment_id>/skip", methods=["POST"])
@role_required("doctor")
def skip_patient(appointment_id):
    doctor = _get_doctor_or_404()
    if not doctor:
        return jsonify({"error": "Doctor profile not found"}), 404
    appointment = _get_own_appointment(doctor, appointment_id)
    if not appointment:
        return jsonify({"error": "Appointment not found"}), 404
    if appointment.status not in ("waiting", "consulting"):
        return jsonify({"error": f"Cannot skip an appointment with status '{appointment.status}'"}), 400

    queue_service.skip_patient(appointment)
    return jsonify(appointment.to_dict()), 200


@doctor_bp.route("/appointments/<int:appointment_id>/absent", methods=["POST"])
@role_required("doctor")
def mark_absent(appointment_id):
    doctor = _get_doctor_or_404()
    if not doctor:
        return jsonify({"error": "Doctor profile not found"}), 404
    appointment = _get_own_appointment(doctor, appointment_id)
    if not appointment:
        return jsonify({"error": "Appointment not found"}), 404
    if appointment.status != "waiting":
        return jsonify({"error": f"Cannot mark absent from status '{appointment.status}'"}), 400

    queue_service.mark_absent(appointment)
    return jsonify(appointment.to_dict()), 200


@doctor_bp.route("/stats", methods=["GET"])
@role_required("doctor")
def daily_stats():
    doctor = _get_doctor_or_404()
    if not doctor:
        return jsonify({"error": "Doctor profile not found"}), 404

    today_appts = Appointment.query.filter(
        Appointment.doctor_id == doctor.id, db.func.date(Appointment.created_at) == today()
    )
    total = today_appts.count()
    completed = today_appts.filter(Appointment.status == "completed").count()
    waiting = today_appts.filter(Appointment.status == "waiting").count()
    cancelled = today_appts.filter(Appointment.status == "cancelled").count()
    absent = today_appts.filter(Appointment.status == "absent").count()

    avg_wait = (
        db.session.query(db.func.avg(Appointment.actual_waiting_time))
        .filter(
            Appointment.doctor_id == doctor.id,
            Appointment.actual_waiting_time.isnot(None),
            db.func.date(Appointment.created_at) == today(),
        )
        .scalar()
    )

    return jsonify({
        "total_today": total,
        "completed": completed,
        "waiting": waiting,
        "cancelled": cancelled,
        "absent": absent,
        "average_wait_minutes": round(float(avg_wait), 1) if avg_wait else 0,
        "current_load": doctor.current_load(),
        "is_available": bool(doctor.is_available),
    }), 200


@doctor_bp.route("/availability", methods=["PUT"])
@role_required("doctor")
def set_availability():
    doctor = _get_doctor_or_404()
    if not doctor:
        return jsonify({"error": "Doctor profile not found"}), 404

    data = request.get_json(silent=True) or {}
    if "is_available" in data:
        doctor.is_available = bool(data["is_available"])
        db.session.commit()
        queue_service.recalculate_queue_predictions(doctor.id)
    return jsonify(doctor.to_dict()), 200
