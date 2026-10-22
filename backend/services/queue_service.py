from sqlalchemy import and_, or_

from extensions import db
from models.appointment import Appointment, WaitingTimeHistory
from models.doctor import Doctor
from ml.predict import predict_waiting_time
from utils.timeutils import now, today

APPOINTMENT_TYPE_MAP = {"general": 0, "follow_up": 1, "emergency": 2}


def _todays_appointments(doctor_id):
    return Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        db.func.date(Appointment.created_at) == today(),
    )


def count_patients_ahead(doctor_id, priority_level, queue_number=None):
    """
    How many patients will be seen before this one.

    Service order matches the doctor's queue: the patient currently being
    consulted always finishes first, then waiting patients ordered by
    priority_level DESC, queue_number ASC.

    - queue_number=None -> a NEW appointment that doesn't exist yet: every
      waiting patient with priority >= ours is ahead (they all arrived earlier).
    - queue_number=N    -> an EXISTING waiting appointment: only higher-priority
      patients, or same-priority patients with a smaller queue number, are ahead.
      (Previously later arrivals of the same priority were counted as "ahead",
      so everyone saw nearly the same, wrong position and wait time.)
    """
    base = _todays_appointments(doctor_id)
    consulting = base.filter(Appointment.status == "consulting").count()

    waiting = base.filter(Appointment.status == "waiting")
    if queue_number is None:
        waiting_ahead = waiting.filter(Appointment.priority_level >= priority_level).count()
    else:
        waiting_ahead = waiting.filter(
            or_(
                Appointment.priority_level > priority_level,
                and_(
                    Appointment.priority_level == priority_level,
                    Appointment.queue_number < queue_number,
                ),
            )
        ).count()
    return consulting + waiting_ahead


def next_queue_number(doctor_id):
    last = _todays_appointments(doctor_id).order_by(Appointment.queue_number.desc()).first()
    return (last.queue_number + 1) if last else 1


def get_historical_average_wait(doctor_id):
    """Average actual_waiting_time for this doctor's completed appointments (fallback to 25 min)."""
    from sqlalchemy import func

    avg = (
        db.session.query(func.avg(Appointment.actual_waiting_time))
        .filter(Appointment.doctor_id == doctor_id, Appointment.actual_waiting_time.isnot(None))
        .scalar()
    )
    return float(avg) if avg else 25.0


def build_features(doctor: Doctor, appointment_type: str, priority_level: int,
                   patients_ahead: int, current_load: int, historical_wait: float = None):
    current = now()
    if historical_wait is None:
        historical_wait = get_historical_average_wait(doctor.id)
    return {
        "patients_ahead": int(patients_ahead),
        "average_consultation_time": float(doctor.average_consultation_time or 15),
        "doctor_available": 1 if doctor.is_available else 0,
        "appointment_type": APPOINTMENT_TYPE_MAP.get(appointment_type, 0),
        "priority_level": int(priority_level),
        "day_of_week": current.weekday(),
        "hour": current.hour,
        "doctor_current_load": int(current_load),
        "historical_average_wait": float(historical_wait),
    }


def build_features_for_new_appointment(doctor: Doctor, appointment_type: str, priority_level: int):
    return build_features(
        doctor,
        appointment_type,
        priority_level,
        patients_ahead=count_patients_ahead(doctor.id, priority_level),
        current_load=doctor.current_load(),
    )


def create_appointment_with_prediction(patient_id, doctor: Doctor, appointment_type="general", priority_level=1):
    features = build_features_for_new_appointment(doctor, appointment_type, priority_level)
    predicted_minutes = predict_waiting_time(features)

    appointment = Appointment(
        patient_id=patient_id,
        doctor_id=doctor.id,
        queue_number=next_queue_number(doctor.id),
        appointment_type=appointment_type,
        priority_level=priority_level,
        status="waiting",
        predicted_waiting_time=predicted_minutes,
    )
    db.session.add(appointment)
    db.session.flush()  # get appointment.id before commit

    history = WaitingTimeHistory(
        appointment_id=appointment.id,
        patients_ahead=features["patients_ahead"],
        average_consultation_time=features["average_consultation_time"],
        doctor_available=features["doctor_available"],
        appointment_type=features["appointment_type"],
        priority_level=features["priority_level"],
        day_of_week=features["day_of_week"],
        hour=features["hour"],
        doctor_current_load=features["doctor_current_load"],
        historical_average_wait=features["historical_average_wait"],
        predicted_waiting_time=predicted_minutes,
    )
    db.session.add(history)
    db.session.commit()
    return appointment


def get_queue_position(appointment: Appointment):
    """Returns (position_in_queue, patients_ahead) for a waiting appointment."""
    if appointment.status != "waiting":
        return None, 0
    ahead = count_patients_ahead(
        appointment.doctor_id, appointment.priority_level, queue_number=appointment.queue_number
    )
    return ahead + 1, ahead


def recalculate_queue_predictions(doctor_id):
    """
    Re-run the ML prediction for every waiting appointment of a doctor (called after a
    status change). Each patient gets features for THEIR OWN position in the queue.
    """
    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        return
    waiting_appointments = (
        _todays_appointments(doctor_id)
        .filter(Appointment.status == "waiting")
        .order_by(Appointment.priority_level.desc(), Appointment.queue_number.asc())
        .all()
    )
    if not waiting_appointments:
        return

    historical_wait = get_historical_average_wait(doctor_id)
    total_load = doctor.current_load()  # includes the patient being predicted

    for appt in waiting_appointments:
        ahead = count_patients_ahead(doctor_id, appt.priority_level, queue_number=appt.queue_number)
        features = build_features(
            doctor,
            appt.appointment_type,
            appt.priority_level,
            patients_ahead=ahead,
            current_load=max(total_load - 1, 0),  # same definition as at booking time (excludes self)
            historical_wait=historical_wait,
        )
        appt.predicted_waiting_time = predict_waiting_time(features)
    db.session.commit()


def start_consultation(appointment: Appointment):
    appointment.status = "consulting"
    appointment.consultation_started_at = now()
    db.session.commit()


def complete_consultation(appointment: Appointment, notes=None):
    from models.appointment import Consultation

    current = now()
    appointment.status = "completed"
    appointment.consultation_ended_at = current
    if appointment.consultation_started_at:
        elapsed = (current - appointment.consultation_started_at).total_seconds() / 60.0
        appointment.actual_waiting_time = round(
            (appointment.consultation_started_at - appointment.created_at).total_seconds() / 60.0, 1
        )
    else:
        elapsed = None

    consultation = Consultation(
        appointment_id=appointment.id,
        notes=notes,
        duration_minutes=round(elapsed, 1) if elapsed is not None else None,
    )
    db.session.add(consultation)

    # update ML training history with the real outcome for future retraining
    history = WaitingTimeHistory.query.filter_by(appointment_id=appointment.id).first()
    if history and appointment.actual_waiting_time is not None:
        history.actual_waiting_time_minutes = appointment.actual_waiting_time

    db.session.commit()
    recalculate_queue_predictions(appointment.doctor_id)


def skip_patient(appointment: Appointment):
    appointment.status = "skipped"
    db.session.commit()
    recalculate_queue_predictions(appointment.doctor_id)


def mark_absent(appointment: Appointment):
    appointment.status = "absent"
    db.session.commit()
    recalculate_queue_predictions(appointment.doctor_id)


def cancel_appointment(appointment: Appointment):
    appointment.status = "cancelled"
    db.session.commit()
    recalculate_queue_predictions(appointment.doctor_id)
