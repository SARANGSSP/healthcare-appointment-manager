"""
Role middleware (Build Plan Chunk 3: "Role middleware enforced on
every route from here on, not bolted on later"). Every route added
in Chunks 5+ should be wrapped in @login_required, and
@role_required(...) where the route is role-specific.
"""
from functools import wraps

import jwt as pyjwt
from flask import g, jsonify, request

from app.auth.tokens import decode_token


def _error(code, message, status):
    return jsonify({"error": {"code": code, "message": message, "details": []}}), status


def _extract_bearer_token():
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    return header.split(" ", 1)[1].strip()


def login_required(fn):
    """Populates flask.g.current_user = {"id": int, "role": str} on success."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = _extract_bearer_token()
        if not token:
            return _error("unauthorized", "Missing bearer token", 401)

        try:
            payload = decode_token(token)
        except pyjwt.ExpiredSignatureError:
            return _error("token_expired", "Token has expired", 401)
        except pyjwt.InvalidTokenError:
            return _error("invalid_token", "Invalid token", 401)

        if payload.get("type") != "access":
            return _error("invalid_token", "An access token is required here", 401)

        g.current_user = {"id": int(payload["sub"]), "role": payload["role"]}
        return fn(*args, **kwargs)

    return wrapper


def role_required(*roles):
    """Stack under @login_required, e.g.:

        @doctors_bp.get("/doctors/me")
        @login_required
        @role_required("doctor")
        def doctor_me(): ...
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            current = getattr(g, "current_user", None)
            if current is None or current["role"] not in roles:
                return _error("forbidden", "You don't have access to this resource", 403)
            return fn(*args, **kwargs)

        return wrapper

    return decorator
