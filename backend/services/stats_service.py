from datetime import date, timedelta
from sqlalchemy import func

from extensions import db
from models.appointment import Appointment
from models.doctor import Doctor, Department
from utils.timeutils import today as local_today


def hospital_overview():
    today = local_today()
    todays_patients = Appointment.query.filter(func.date(Appointment.created_at) == today).count()
    waiting = Appointment.query.filter(
        Appointment.status == "waiting", func.date(Appointment.created_at) == today
    ).count()
    doctors_available = Doctor.query.filter_by(is_available=True).count()
    completed = Appointment.query.filter(
        Appointment.status == "completed", func.date(Appointment.created_at) == today
    ).count()
    cancelled = Appointment.query.filter(
        Appointment.status == "cancelled", func.date(Appointment.created_at) == today
    ).count()

    avg_wait = (
        db.session.query(func.avg(Appointment.actual_waiting_time))
        .filter(Appointment.actual_waiting_time.isnot(None), func.date(Appointment.created_at) == today)
        .scalar()
    )

    return {
        "todays_patients": todays_patients,
        "waiting_patients": waiting,
        "doctors_available": doctors_available,
        "current_average_waiting_time": round(float(avg_wait), 1) if avg_wait else 0,
        "completed_consultations": completed,
        "cancelled_appointments": cancelled,
    }


def patients_per_day(days=14):
    days = max(1, min(int(days), 365))
    since = local_today() - timedelta(days=days)
    rows = (
        db.session.query(func.date(Appointment.created_at).label("day"), func.count(Appointment.id))
        .filter(func.date(Appointment.created_at) >= since)
        .group_by("day")
        .order_by("day")
        .all()
    )
    return [{"date": str(r[0]), "count": r[1]} for r in rows]


def average_wait_by_hour():
    rows = (
        db.session.query(
            func.hour(Appointment.created_at).label("hour"),
            func.avg(Appointment.actual_waiting_time),
        )
        .filter(Appointment.actual_waiting_time.isnot(None))
        .group_by("hour")
        .order_by("hour")
        .all()
    )
    return [{"hour": int(r[0]), "avg_wait": round(float(r[1]), 1)} for r in rows]


def patients_by_department():
    rows = (
        db.session.query(Department.name, func.count(Appointment.id))
        .join(Doctor, Doctor.department_id == Department.id)
        .join(Appointment, Appointment.doctor_id == Doctor.id)
        .group_by(Department.name)
        .all()
    )
    return [{"department": r[0], "count": r[1]} for r in rows]


def doctor_workload():
    rows = (
        db.session.query(Doctor.id, func.count(Appointment.id))
        .join(Appointment, Appointment.doctor_id == Doctor.id)
        .filter(func.date(Appointment.created_at) == local_today())
        .group_by(Doctor.id)
        .all()
    )
    result = []
    for doctor_id, count in rows:
        doctor = Doctor.query.get(doctor_id)
        result.append({
            "doctor_id": doctor_id,
            "doctor_name": doctor.user.full_name if doctor and doctor.user else "Unknown",
            "patients_today": count,
        })
    return result


def appointment_status_breakdown():
    rows = (
        db.session.query(Appointment.status, func.count(Appointment.id))
        .filter(func.date(Appointment.created_at) == local_today())
        .group_by(Appointment.status)
        .all()
    )
    return [{"status": r[0], "count": r[1]} for r in rows]


def peak_hours():
    rows = (
        db.session.query(func.hour(Appointment.created_at).label("hour"), func.count(Appointment.id))
        .group_by("hour")
        .order_by(func.count(Appointment.id).desc())
        .limit(5)
        .all()
    )
    return [{"hour": int(r[0]), "count": r[1]} for r in rows]


def monthly_patient_stats(months=6):
    """Appointments per month for the LAST `months` months (including the current one)."""
    months = max(1, min(int(months), 36))
    year, month = local_today().year, local_today().month - (months - 1)
    while month <= 0:
        month += 12
        year -= 1
    since = date(year, month, 1)
    rows = (
        db.session.query(
            func.date_format(Appointment.created_at, "%Y-%m").label("month"),
            func.count(Appointment.id),
        )
        .filter(func.date(Appointment.created_at) >= since)
        .group_by("month")
        .order_by("month")
        .all()
    )
    return [{"month": r[0], "count": r[1]} for r in rows]
