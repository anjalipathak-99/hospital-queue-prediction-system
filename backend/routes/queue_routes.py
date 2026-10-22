from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from extensions import db
from models.appointment import Appointment
from models.doctor import Doctor
from utils.timeutils import today

queue_bp = Blueprint("queue", __name__, url_prefix="/api/queues")


@queue_bp.route("/doctor/<int:doctor_id>", methods=["GET"])
@jwt_required()
def doctor_queue(doctor_id):
    """Live queue snapshot for a given doctor (visible to any logged-in user)."""
    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    appointments = (
        Appointment.query.filter(
            Appointment.doctor_id == doctor_id,
            db.func.date(Appointment.created_at) == today(),
            Appointment.status.in_(["waiting", "consulting"]),
        )
        .order_by(Appointment.priority_level.desc(), Appointment.queue_number.asc())
        .all()
    )
    return jsonify({
        "doctor": doctor.to_dict(),
        "queue": [a.to_dict() for a in appointments],
        "queue_length": len(appointments),
    }), 200
