from utils.timeutils import now
from extensions import db


class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey("doctors.id"), nullable=False)

    queue_number = db.Column(db.Integer, nullable=False)
    appointment_type = db.Column(
        db.Enum("general", "follow_up", "emergency", name="appointment_type_enum"),
        default="general",
    )
    priority_level = db.Column(db.Integer, default=1)  # 1 = normal, 2 = high, 3 = emergency
    status = db.Column(
        db.Enum(
            "waiting", "consulting", "completed", "cancelled", "skipped", "absent",
            name="appointment_status_enum",
        ),
        default="waiting",
        index=True,
    )

    predicted_waiting_time = db.Column(db.Float, nullable=True)  # minutes, from ML model
    actual_waiting_time = db.Column(db.Float, nullable=True)  # minutes, filled once completed

    consultation_started_at = db.Column(db.DateTime, nullable=True)
    consultation_ended_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=now, index=True)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)

    consultation = db.relationship("Consultation", backref="appointment", uselist=False, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "patient_name": self.patient.user.full_name if self.patient and self.patient.user else None,
            "doctor_id": self.doctor_id,
            "doctor_name": self.doctor.user.full_name if self.doctor and self.doctor.user else None,
            "department_name": self.doctor.department.name if self.doctor and self.doctor.department else None,
            "queue_number": self.queue_number,
            "appointment_type": self.appointment_type,
            "priority_level": self.priority_level,
            "status": self.status,
            "predicted_waiting_time": self.predicted_waiting_time,
            "actual_waiting_time": self.actual_waiting_time,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "consultation_started_at": self.consultation_started_at.isoformat() if self.consultation_started_at else None,
            "consultation_ended_at": self.consultation_ended_at.isoformat() if self.consultation_ended_at else None,
        }


class Consultation(db.Model):
    __tablename__ = "consultations"

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey("appointments.id"), nullable=False, unique=True)
    notes = db.Column(db.Text, nullable=True)
    duration_minutes = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=now)

    def to_dict(self):
        return {
            "id": self.id,
            "appointment_id": self.appointment_id,
            "notes": self.notes,
            "duration_minutes": self.duration_minutes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class WaitingTimeHistory(db.Model):
    """Stores feature snapshots + actual outcomes, used to retrain the ML model over time."""
    __tablename__ = "waiting_time_history"

    id = db.Column(db.Integer, primary_key=True)
    # ondelete=SET NULL: deleting a doctor/patient (cascades to appointments) used to fail
    # with a MySQL foreign-key error because history rows still pointed at the appointment.
    appointment_id = db.Column(db.Integer, db.ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True)

    patients_ahead = db.Column(db.Integer, nullable=False)
    average_consultation_time = db.Column(db.Float, nullable=False)
    doctor_available = db.Column(db.Integer, nullable=False)  # 1/0
    appointment_type = db.Column(db.Integer, nullable=False)  # encoded
    priority_level = db.Column(db.Integer, nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)
    hour = db.Column(db.Integer, nullable=False)
    doctor_current_load = db.Column(db.Integer, nullable=False)
    historical_average_wait = db.Column(db.Float, nullable=False)

    predicted_waiting_time = db.Column(db.Float, nullable=True)
    actual_waiting_time_minutes = db.Column(db.Float, nullable=True)

    created_at = db.Column(db.DateTime, default=now)

    def to_dict(self):
        return {
            "id": self.id,
            "appointment_id": self.appointment_id,
            "patients_ahead": self.patients_ahead,
            "average_consultation_time": self.average_consultation_time,
            "doctor_available": self.doctor_available,
            "appointment_type": self.appointment_type,
            "priority_level": self.priority_level,
            "day_of_week": self.day_of_week,
            "hour": self.hour,
            "doctor_current_load": self.doctor_current_load,
            "historical_average_wait": self.historical_average_wait,
            "predicted_waiting_time": self.predicted_waiting_time,
            "actual_waiting_time_minutes": self.actual_waiting_time_minutes,
        }
