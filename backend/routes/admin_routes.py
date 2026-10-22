from flask import Blueprint, request, jsonify

from extensions import db
from models.user import User, Patient
from models.doctor import Doctor, Department
from models.appointment import Appointment
from services import stats_service
from utils.decorators import role_required
from utils.timeutils import today
from utils.validators import is_valid_email, is_valid_password, require_fields

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def _positive_int(value, default):
    """Parse a positive integer from JSON/form input. Returns (value, ok)."""
    if value in (None, ""):
        return default, True
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None, False
    return (parsed, True) if parsed > 0 else (None, False)


# ---------- Departments ----------

@admin_bp.route("/departments", methods=["GET"])
@role_required("admin")
def list_departments():
    return jsonify([d.to_dict() for d in Department.query.all()]), 200


@admin_bp.route("/departments", methods=["POST"])
@role_required("admin")
def create_department():
    data = request.get_json(silent=True) or {}
    missing = require_fields(data, ["name"])
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400
    if Department.query.filter_by(name=data["name"]).first():
        return jsonify({"error": "Department already exists"}), 409

    department = Department(name=data["name"], description=data.get("description"))
    db.session.add(department)
    db.session.commit()
    return jsonify(department.to_dict()), 201


@admin_bp.route("/departments/<int:department_id>", methods=["PUT"])
@role_required("admin")
def update_department(department_id):
    department = Department.query.get(department_id)
    if not department:
        return jsonify({"error": "Department not found"}), 404
    data = request.get_json(silent=True) or {}
    new_name = (data.get("name") or department.name).strip()
    clash = Department.query.filter(Department.name == new_name, Department.id != department.id).first()
    if clash:
        return jsonify({"error": "Another department already uses this name"}), 409
    department.name = new_name
    department.description = data.get("description", department.description)
    db.session.commit()
    return jsonify(department.to_dict()), 200


@admin_bp.route("/departments/<int:department_id>", methods=["DELETE"])
@role_required("admin")
def delete_department(department_id):
    department = Department.query.get(department_id)
    if not department:
        return jsonify({"error": "Department not found"}), 404
    if department.doctors:
        return jsonify({"error": "Cannot delete a department that still has doctors. Reassign or remove them first."}), 409
    db.session.delete(department)
    db.session.commit()
    return jsonify({"message": "Department deleted"}), 200


# ---------- Doctors ----------

@admin_bp.route("/doctors", methods=["GET"])
@role_required("admin")
def list_doctors():
    return jsonify([d.to_dict() for d in Doctor.query.all()]), 200


@admin_bp.route("/doctors", methods=["POST"])
@role_required("admin")
def add_doctor():
    data = request.get_json(silent=True) or {}
    missing = require_fields(data, ["full_name", "email", "password", "department_id"])
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    if not is_valid_email(data["email"]):
        return jsonify({"error": "Invalid email format"}), 400
    if not is_valid_password(data["password"]):
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "An account with this email already exists"}), 409

    department = Department.query.get(data["department_id"])
    if not department:
        return jsonify({"error": "Department not found"}), 404

    avg_time, ok_avg = _positive_int(data.get("average_consultation_time"), 15)
    max_patients, ok_max = _positive_int(data.get("max_daily_patients"), 40)
    if not (ok_avg and ok_max):
        return jsonify({"error": "average_consultation_time and max_daily_patients must be positive whole numbers"}), 400

    user = User(full_name=data["full_name"], email=data["email"], phone=data.get("phone"), role="doctor")
    user.set_password(data["password"])
    db.session.add(user)
    db.session.flush()

    doctor = Doctor(
        user_id=user.id,
        department_id=department.id,
        specialization=data.get("specialization"),
        average_consultation_time=avg_time,
        max_daily_patients=max_patients,
    )
    db.session.add(doctor)
    db.session.commit()
    return jsonify(doctor.to_dict()), 201


@admin_bp.route("/doctors/<int:doctor_id>", methods=["PUT"])
@role_required("admin")
def edit_doctor(doctor_id):
    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    data = request.get_json(silent=True) or {}
    if "department_id" in data:
        department = Department.query.get(data["department_id"])
        if not department:
            return jsonify({"error": "Department not found"}), 404
    avg_time, ok_avg = _positive_int(data.get("average_consultation_time"), doctor.average_consultation_time)
    max_patients, ok_max = _positive_int(data.get("max_daily_patients"), doctor.max_daily_patients)
    if not (ok_avg and ok_max):
        return jsonify({"error": "average_consultation_time and max_daily_patients must be positive whole numbers"}), 400

    if "full_name" in data and data["full_name"]:
        doctor.user.full_name = data["full_name"]
    if "phone" in data:
        doctor.user.phone = data["phone"]
    if "department_id" in data:
        doctor.department_id = department.id
    if "specialization" in data:
        doctor.specialization = data["specialization"]
    doctor.average_consultation_time = avg_time
    doctor.max_daily_patients = max_patients
    if "is_available" in data:
        doctor.is_available = bool(data["is_available"])

    db.session.commit()
    return jsonify(doctor.to_dict()), 200


@admin_bp.route("/doctors/<int:doctor_id>", methods=["DELETE"])
@role_required("admin")
def delete_doctor(doctor_id):
    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404
    user = doctor.user
    db.session.delete(doctor)
    if user:
        db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "Doctor deleted"}), 200


# ---------- Patients ----------

@admin_bp.route("/patients", methods=["GET"])
@role_required("admin")
def list_patients():
    return jsonify([p.to_dict() for p in Patient.query.all()]), 200


# ---------- Appointments / Queues ----------

@admin_bp.route("/appointments", methods=["GET"])
@role_required("admin")
def list_appointments():
    status = request.args.get("status")
    query = Appointment.query
    if status:
        query = query.filter_by(status=status)
    appointments = query.order_by(Appointment.created_at.desc()).limit(500).all()
    return jsonify([a.to_dict() for a in appointments]), 200


@admin_bp.route("/queues", methods=["GET"])
@role_required("admin")
def monitor_queues():
    appointments = (
        Appointment.query.filter(
            Appointment.status.in_(["waiting", "consulting"]),
            db.func.date(Appointment.created_at) == today(),
        )
        .order_by(Appointment.doctor_id.asc(), Appointment.priority_level.desc(), Appointment.queue_number.asc())
        .all()
    )
    return jsonify([a.to_dict() for a in appointments]), 200


# ---------- Statistics ----------

@admin_bp.route("/stats/overview", methods=["GET"])
@role_required("admin")
def stats_overview():
    return jsonify(stats_service.hospital_overview()), 200


@admin_bp.route("/stats/patients-per-day", methods=["GET"])
@role_required("admin")
def stats_patients_per_day():
    days = request.args.get("days", 14, type=int)
    return jsonify(stats_service.patients_per_day(days)), 200


@admin_bp.route("/stats/wait-by-hour", methods=["GET"])
@role_required("admin")
def stats_wait_by_hour():
    return jsonify(stats_service.average_wait_by_hour()), 200


@admin_bp.route("/stats/by-department", methods=["GET"])
@role_required("admin")
def stats_by_department():
    return jsonify(stats_service.patients_by_department()), 200


@admin_bp.route("/stats/doctor-workload", methods=["GET"])
@role_required("admin")
def stats_doctor_workload():
    return jsonify(stats_service.doctor_workload()), 200


@admin_bp.route("/stats/status-breakdown", methods=["GET"])
@role_required("admin")
def stats_status_breakdown():
    return jsonify(stats_service.appointment_status_breakdown()), 200


@admin_bp.route("/stats/peak-hours", methods=["GET"])
@role_required("admin")
def stats_peak_hours():
    return jsonify(stats_service.peak_hours()), 200


@admin_bp.route("/stats/monthly", methods=["GET"])
@role_required("admin")
def stats_monthly():
    months = request.args.get("months", 6, type=int)
    return jsonify(stats_service.monthly_patient_stats(months)), 200
