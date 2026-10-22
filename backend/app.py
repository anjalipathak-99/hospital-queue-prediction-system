import logging
import os

from flask import Flask, jsonify
from sqlalchemy.exc import OperationalError, ProgrammingError, SQLAlchemyError
from werkzeug.exceptions import HTTPException

from config import config_by_name
from extensions import db, jwt, cors, bcrypt


def create_app(env=None):
    app = Flask(__name__)
    env = env or os.environ.get("FLASK_ENV", "development")
    app.config.from_object(config_by_name.get(env, config_by_name["development"]))

    # --- init extensions ---
    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}}, supports_credentials=True)

    # --- import models so SQLAlchemy is aware of them before create_all/migrations ---
    from models import User, Patient, Doctor, Department, Appointment, Consultation, WaitingTimeHistory  # noqa: F401

    # --- register blueprints ---
    from routes.auth_routes import auth_bp
    from routes.patient_routes import patient_bp
    from routes.doctor_routes import doctor_bp
    from routes.admin_routes import admin_bp
    from routes.appointment_routes import appointment_bp
    from routes.queue_routes import queue_bp
    from routes.ml_routes import ml_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(appointment_bp)
    app.register_blueprint(queue_bp)
    app.register_blueprint(ml_bp)

    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "service": "hospital-queue-prediction-system"}), 200

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        """
        Without this, in debug mode Flask returns an HTML traceback page, the React app finds
        no JSON `error` field and just shows "Registration failed". Always return JSON instead.
        """
        if isinstance(e, HTTPException):
            return jsonify({"error": e.description or e.name}), e.code

        db.session.rollback()
        logging.getLogger(__name__).exception("Unhandled error on %s", e.__class__.__name__)

        if isinstance(e, (OperationalError, ProgrammingError)):
            msg = (
                "Database error: check that MySQL is running, the DB_* values in backend/.env are "
                "correct, the database exists, and you have run `python seed.py`."
            )
        elif isinstance(e, SQLAlchemyError):
            msg = "Database error while saving your data."
        else:
            msg = "Internal server error"
        if app.config.get("DEBUG"):
            msg += f" [{e.__class__.__name__}: {str(e).splitlines()[0][:200]}]"
        return jsonify({"error": msg}), 500

    @jwt.unauthorized_loader
    def unauthorized_callback(reason):
        return jsonify({"error": "Missing or invalid authorization token"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        return jsonify({"error": "Invalid token"}), 422

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"error": "Token has expired"}), 401

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=app.config.get("DEBUG", True))
