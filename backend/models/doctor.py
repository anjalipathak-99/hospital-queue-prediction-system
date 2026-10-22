from utils.timeutils import now
from extensions import db


class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=now)

    doctors = db.relationship("Doctor", backref="department", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "doctor_count": len(self.doctors),
        }


class Doctor(db.Model):
    __tablename__ = "doctors"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=False)
    specialization = db.Column(db.String(150), nullable=True)
    average_consultation_time = db.Column(db.Integer, default=15)  # minutes
    is_available = db.Column(db.Boolean, default=True)
    max_daily_patients = db.Column(db.Integer, default=40)
    created_at = db.Column(db.DateTime, default=now)

    appointments = db.relationship("Appointment", backref="doctor", lazy=True, cascade="all, delete-orphan")

    def current_load(self):
        """Number of patients currently waiting or being consulted today."""
        from models.appointment import Appointment
        from utils.timeutils import today

        return Appointment.query.filter(
            Appointment.doctor_id == self.id,
            Appointment.status.in_(["waiting", "consulting"]),
            db.func.date(Appointment.created_at) == today(),
        ).count()

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "full_name": self.user.full_name if self.user else None,
            "email": self.user.email if self.user else None,
            "department_id": self.department_id,
            "department_name": self.department.name if self.department else None,
            "specialization": self.specialization,
            "average_consultation_time": self.average_consultation_time,
            "is_available": self.is_available,
            "max_daily_patients": self.max_daily_patients,
            "current_load": self.current_load(),
        }
