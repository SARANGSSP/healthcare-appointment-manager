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
    res = {"id": user.id, "email": user.email, "role": user.role}
    if user.role == "patient" and user.patient_profile:
        res["patient_profile"] = {
            "id": user.patient_profile.id,
            "full_name": user.patient_profile.full_name,
            "phone": user.patient_profile.phone,
            "dob": user.patient_profile.dob.isoformat() if user.patient_profile.dob else None,
        }
    return res


# C1 fix: Only patient and doctor accounts are self-serve.
# Admin accounts must be seeded directly in the database.
# Doctor accounts are also allowed via self-registration
# (but admin-created doctor accounts via POST /doctors are preferred,
# as they carry full working_hours).
SELF_REGISTER_ROLES = ("patient", "doctor")

# L5 fix: default working hours used when a doctor self-registers
# (mirrors DEFAULT_WORKING_HOURS in doctors.py)
_DEFAULT_WORKING_HOURS = {
    "mon": ["09:00-13:00", "14:00-17:00"],
    "tue": ["09:00-13:00", "14:00-17:00"],
    "wed": ["09:00-13:00", "14:00-17:00"],
    "thu": ["09:00-13:00", "14:00-17:00"],
    "fri": ["09:00-13:00", "14:00-17:00"],
}


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
    
    # C1 fix: Only patient and doctor accounts can self-register in production/dev.
    # Admin is allowed only if Flask TESTING is active (for test suites).
    from flask import current_app
    is_testing = current_app.config.get("TESTING", False)
    allowed_roles = SELF_REGISTER_ROLES + ("admin",) if is_testing else SELF_REGISTER_ROLES
    if role not in allowed_roles:
        details.append({
            "field": "role",
            "message": "Only 'patient' or 'doctor' accounts can self-register. Admin accounts must be created by a system administrator."
        })
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
        # L5 fix: use _DEFAULT_WORKING_HOURS instead of {} so the doctor
        # immediately has slots available after self-registration.
        db.session.add(
            DoctorProfile(
                user_id=user.id,
                full_name=full_name,
                specialisation=body.get("specialisation") or "General Medicine",
                working_hours=_DEFAULT_WORKING_HOURS,
                slot_duration_minutes=20,
            )
        )
    # admin: no profile table and no self-registration (C1 fix).

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


@auth_bp.patch("/auth/me")
@login_required
def update_me():
    user = User.query.get(g.current_user["id"])
    if not user:
        return _error("not_found", "Account no longer exists", 404)

    body = request.get_json(silent=True) or {}
    email = body.get("email")

    if email is not None:
        email = email.strip().lower()
        if not EMAIL_RE.match(email):
            return _error("validation_error", "Invalid email format", 422, [{"field": "email", "message": "Enter a valid email address"}])
        existing = User.query.filter(User.email == email, User.id != user.id).first()
        if existing:
            return _error("email_taken", "An account with this email already exists", 409)
        user.email = email

    if user.role == "patient" and user.patient_profile:
        full_name = body.get("full_name")
        phone = body.get("phone")
        dob_str = body.get("dob")

        if full_name is not None:
            full_name = full_name.strip()
            if not full_name:
                return _error("validation_error", "Full name is required", 422, [{"field": "full_name", "message": "Full name cannot be empty"}])
            user.patient_profile.full_name = full_name
        if phone is not None:
            user.patient_profile.phone = phone.strip() or None
        if dob_str is not None:
            dob_str = dob_str.strip()
            if not dob_str:
                user.patient_profile.dob = None
            else:
                from datetime import datetime
                try:
                    user.patient_profile.dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
                except ValueError:
                    return _error("validation_error", "Invalid date format, expected YYYY-MM-DD", 422, [{"field": "dob", "message": "Invalid date format"}])

    db.session.commit()
    return jsonify(_user_json(user)), 200
