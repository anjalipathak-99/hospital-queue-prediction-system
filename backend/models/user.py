from utils.timeutils import now
from extensions import db, bcrypt


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("patient", "doctor", "admin", name="user_role"), nullable=False, default="patient")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)

    patient_profile = db.relationship("Patient", backref="user", uselist=False, cascade="all, delete-orphan")
    doctor_profile = db.relationship("Doctor", backref="user", uselist=False, cascade="all, delete-orphan")

    def set_password(self, raw_password):
        self.password_hash = bcrypt.generate_password_hash(raw_password).decode("utf-8")

    def check_password(self, raw_password):
        return bcrypt.check_password_hash(self.password_hash, raw_password)

    def to_dict(self):
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.Enum("male", "female", "other", name="gender_enum"), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    blood_group = db.Column(db.String(5), nullable=True)

    appointments = db.relationship("Appointment", backref="patient", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "full_name": self.user.full_name if self.user else None,
            "email": self.user.email if self.user else None,
            "phone": self.user.phone if self.user else None,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "gender": self.gender,
            "address": self.address,
            "blood_group": self.blood_group,
        }
