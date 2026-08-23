"""
Auth endpoints (Build Plan Chunk 3 / Design Document §5, §11 ADR-none
— plain JWT + bcrypt, no OAuth for the app's own accounts).
"""
import re

import bcrypt
import jwt as pyjwt
from flask import Blueprint, g, jsonify, request

from app.auth.decorators import login_required
from app.auth.tokens import create_access_token, create_refresh_token, decode_token
from app.extensions import db
from app.models import DoctorProfile, PatientProfile, User

auth_bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _error(code, message, status, details=None):
    return jsonify({"error": {"code": code, "message": message, "details": details or []}}), status


def _hash_password(raw_password):
    return bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _check_password(raw_password, password_hash):
    try:
        return bcrypt.checkpw(raw_password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def _tokens_for(user):
    return {
        "access_token": create_access_token(user),
        "refresh_token": create_refresh_token(user),
        "role": user.role,
    }


def _user_json(user):
    return {"id": user.id, "email": user.email, "role": user.role}


@auth_bp.post("/auth/register")
def register():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    role = body.get("role") or ""
    full_name = (body.get("full_name") or "").strip()

    details = []
    if not EMAIL_RE.match(email):
        details.append({"field": "email", "message": "Enter a valid email address"})
    if len(password) < 8:
        details.append({"field": "password", "message": "Password must be at least 8 characters"})
    if role not in ("patient", "doctor", "admin"):
        details.append({"field": "role", "message": "Role must be patient, doctor, or admin"})
    if not full_name:
        details.append({"field": "full_name", "message": "Full name is required"})
    if details:
        return _error("validation_error", "Check the highlighted fields", 422, details)

    if User.query.filter_by(email=email).first():
        return _error("email_taken", "An account with this email already exists", 409)

    user = User(email=email, password_hash=_hash_password(password), role=role)
    db.session.add(user)
    db.session.flush()  # assigns user.id before the profile row references it

    if role == "patient":
        db.session.add(
            PatientProfile(
                user_id=user.id,
                full_name=full_name,
                phone=body.get("phone"),
                dob=body.get("dob") or None,
            )
        )
    elif role == "doctor":
        db.session.add(
            DoctorProfile(
                user_id=user.id,
                full_name=full_name,
                specialisation=body.get("specialisation") or "General Medicine",
                working_hours={},
                slot_duration_minutes=20,
            )
        )
    # admin: no profile table — Design Document §4, admin is a bare role.

    db.session.commit()

    return jsonify({"user": _user_json(user), **_tokens_for(user)}), 201


@auth_bp.post("/auth/login")
def login():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not _check_password(password, user.password_hash):
        return _error("invalid_credentials", "Incorrect email or password", 401)

    return jsonify({"user": _user_json(user), **_tokens_for(user)}), 200


@auth_bp.post("/auth/refresh")
def refresh():
    body = request.get_json(silent=True) or {}
    token = body.get("refresh_token") or ""

    try:
        payload = decode_token(token)
    except pyjwt.ExpiredSignatureError:
        return _error("token_expired", "Refresh token has expired, please log in again", 401)
    except pyjwt.InvalidTokenError:
        return _error("invalid_token", "Invalid refresh token", 401)

    if payload.get("type") != "refresh":
        return _error("invalid_token", "A refresh token is required here", 401)

    user = User.query.get(int(payload["sub"]))
    if not user:
        return _error("invalid_token", "Account no longer exists", 401)

    return jsonify({"access_token": create_access_token(user)}), 200


@auth_bp.get("/auth/me")
@login_required
def me():
    user = User.query.get(g.current_user["id"])
    if not user:
        return _error("not_found", "Account no longer exists", 404)
    return jsonify(_user_json(user))
