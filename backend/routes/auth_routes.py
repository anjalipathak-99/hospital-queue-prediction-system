from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt

from extensions import db
from models.user import User, Patient
from models.doctor import Doctor, Department
from utils.validators import is_valid_email, is_valid_password, require_fields

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Registers a patient (default) or, if role='doctor' is passed by an admin flow,
    a doctor account. For simplicity, public self-registration is patient-only;
    doctor accounts are created via the admin routes.
    """
    data = request.get_json(silent=True) or {}

    missing = require_fields(data, ["full_name", "email", "password"])
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    if not is_valid_email(data["email"]):
        return jsonify({"error": "Invalid email format"}), 400

    if not is_valid_password(data["password"]):
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "An account with this email already exists"}), 409

    email = data["email"].strip().lower()
    gender = (data.get("gender") or "").strip().lower() or None
    if gender not in (None, "male", "female", "other"):
        return jsonify({"error": "Invalid gender value"}), 400

    if User.query.filter(db.func.lower(User.email) == email).first():
        return jsonify({"error": "An account with this email already exists"}), 409

    user = User(
        full_name=data["full_name"].strip(),
        email=email,
        phone=(data.get("phone") or "").strip() or None,
        role="patient",
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.flush()

    patient = Patient(
        user_id=user.id,
        gender=gender,
        address=(data.get("address") or "").strip() or None,
        blood_group=(data.get("blood_group") or "").strip() or None,
    )
    db.session.add(patient)
    try:
        db.session.commit()
    except IntegrityError:  # two simultaneous sign-ups with the same email
        db.session.rollback()
        return jsonify({"error": "An account with this email already exists"}), 409

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return jsonify({"message": "Registration successful", "token": token, "user": user.to_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    missing = require_fields(data, ["email", "password"])
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    user = User.query.filter(db.func.lower(User.email) == data["email"].strip().lower()).first()
    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.is_active:
        return jsonify({"error": "This account has been deactivated"}), 403

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})

    extra = {}
    if user.role == "patient" and user.patient_profile:
        extra["patient_id"] = user.patient_profile.id
    if user.role == "doctor" and user.doctor_profile:
        extra["doctor_id"] = user.doctor_profile.id

    return jsonify({"message": "Login successful", "token": token, "user": user.to_dict(), **extra}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    payload = user.to_dict()
    if user.role == "patient" and user.patient_profile:
        payload["patient_id"] = user.patient_profile.id
    if user.role == "doctor" and user.doctor_profile:
        payload["doctor_id"] = user.doctor_profile.id
        payload["department_id"] = user.doctor_profile.department_id

    return jsonify(payload), 200
