"""
Initializes the database (creates tables) and seeds it with:
  - an admin account
  - a set of departments
  - a few doctors
  - one sample patient

Run (after configuring your MySQL connection in config.py / env vars):
    python seed.py
"""

from app import create_app
from extensions import db
from models.user import User, Patient
from models.doctor import Doctor, Department

app = create_app()

DEPARTMENTS = [
    ("General Medicine", "Primary care and general checkups"),
    ("Cardiology", "Heart and cardiovascular care"),
    ("Orthopedics", "Bones, joints, and musculoskeletal care"),
    ("Pediatrics", "Child healthcare"),
    ("Dermatology", "Skin, hair, and nail care"),
]

DOCTORS = [
    ("Dr. Amit Sharma", "amit.sharma@hospital.com", "General Medicine", "General Physician", 15),
    ("Dr. Neha Verma", "neha.verma@hospital.com", "Cardiology", "Cardiologist", 20),
    ("Dr. Ravi Kumar", "ravi.kumar@hospital.com", "Orthopedics", "Orthopedic Surgeon", 18),
    ("Dr. Priya Nair", "priya.nair@hospital.com", "Pediatrics", "Pediatrician", 12),
    ("Dr. Sanjay Gupta", "sanjay.gupta@hospital.com", "Dermatology", "Dermatologist", 10),
]


def seed():
    with app.app_context():
        db.create_all()

        # --- Admin ---
        if not User.query.filter_by(email="admin@hospital.com").first():
            admin = User(full_name="Hospital Admin", email="admin@hospital.com", role="admin")
            admin.set_password("admin123")
            db.session.add(admin)
            print("Created admin: admin@hospital.com / admin123")

        # --- Departments ---
        dept_map = {}
        for name, desc in DEPARTMENTS:
            dept = Department.query.filter_by(name=name).first()
            if not dept:
                dept = Department(name=name, description=desc)
                db.session.add(dept)
                db.session.flush()
                print(f"Created department: {name}")
            dept_map[name] = dept

        db.session.commit()

        # --- Doctors ---
        for full_name, email, dept_name, specialization, avg_time in DOCTORS:
            if User.query.filter_by(email=email).first():
                continue
            user = User(full_name=full_name, email=email, role="doctor")
            user.set_password("doctor123")
            db.session.add(user)
            db.session.flush()

            doctor = Doctor(
                user_id=user.id,
                department_id=dept_map[dept_name].id,
                specialization=specialization,
                average_consultation_time=avg_time,
            )
            db.session.add(doctor)
            print(f"Created doctor: {email} / doctor123")

        # --- Sample patient ---
        if not User.query.filter_by(email="rahul.sharma@example.com").first():
            patient_user = User(full_name="Rahul Sharma", email="rahul.sharma@example.com", role="patient")
            patient_user.set_password("patient123")
            db.session.add(patient_user)
            db.session.flush()
            db.session.add(Patient(user_id=patient_user.id))
            print("Created patient: rahul.sharma@example.com / patient123")

        db.session.commit()
        print("\nSeeding complete.")


if __name__ == "__main__":
    seed()
