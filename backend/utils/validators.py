import re

EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def is_valid_email(email):
    return bool(email) and bool(EMAIL_REGEX.match(email))


def is_valid_password(password):
    """At least 6 characters. Extend this with more rules as needed."""
    return bool(password) and len(password) >= 6


def require_fields(data, fields):
    """Returns a list of missing/empty required fields."""
    missing = []
    for field in fields:
        if data.get(field) in (None, "", []):
            missing.append(field)
    return missing
