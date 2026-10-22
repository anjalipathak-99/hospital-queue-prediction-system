from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request


def role_required(*allowed_roles):
    """Restrict an endpoint to one or more roles. Must be used with a valid JWT.

    Usage:
        @role_required("admin")
        @role_required("doctor", "admin")
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            role = claims.get("role")
            if role not in allowed_roles:
                return jsonify({"error": "Forbidden: insufficient role privileges"}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator
