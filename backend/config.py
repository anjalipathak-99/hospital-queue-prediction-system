import os
from datetime import timedelta
from urllib.parse import quote_plus

basedir = os.path.abspath(os.path.dirname(__file__))

# Load backend/.env automatically. (Flask only auto-loads .env when started via
# the `flask` CLI - NOT with `python app.py` / `python seed.py` / gunicorn - so
# without this the DB credentials in .env were silently ignored.)
try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(basedir, ".env"))
except ImportError:  # python-dotenv not installed -> rely on real env vars
    pass


def _normalize_db_url(url):
    """Accept mysql:// or mysql+pymysql:// style URLs from hosting providers."""
    if url.startswith("mysql://"):
        return "mysql+pymysql://" + url[len("mysql://"):]
    return url


class Config:
    # --- General ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-key")

    # --- Database (MySQL) ---
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "3306")
    DB_NAME = os.environ.get("DB_NAME", "hospital_queue_db")

    # quote_plus: passwords containing @ : / # etc. would otherwise corrupt the URL
    SQLALCHEMY_DATABASE_URI = _normalize_db_url(
        os.environ.get(
            "DATABASE_URL",
            f"mysql+pymysql://{quote_plus(DB_USER)}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
        )
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # --- JWT ---
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "change-this-jwt-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    # --- CORS ---
    CORS_ORIGINS = [
        o.strip()
        for o in os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
        if o.strip()
    ]

    # --- ML ---
    ML_MODEL_PATH = os.path.join(basedir, "ml", "model.pkl")
    ML_FEATURE_COLUMNS = [
        "patients_ahead",
        "average_consultation_time",
        "doctor_available",
        "appointment_type",
        "priority_level",
        "day_of_week",
        "hour",
        "doctor_current_load",
        "historical_average_wait",
    ]


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
