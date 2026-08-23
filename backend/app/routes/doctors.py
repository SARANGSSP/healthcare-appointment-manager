"""
Doctor & Admin Profile Management endpoints (Build Plan Chunk 5 / Design Document §5).
Admin CRUD operations for Doctor profiles + doctor search for patients.
"""
import re

import bcrypt
from flask import Blueprint, g, jsonify, request

from app.auth.decorators import login_required, role_required
from app.extensions import db
from app.models import DoctorProfile, User

doctors_bp = Blueprint("doctors", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

DEFAULT_WORKING_HOURS = {
    "mon": ["09:00-13:00", "14:00-17:00"],
    "tue": ["09:00-13:00", "14:00-17:00"],
    "wed": ["09:00-13:00", "14:00-17:00"],
    "thu": ["09:00-13:00", "14:00-17:00"],
    "fri": ["09:00-13:00", "14:00-17:00"],
}


def _error(code, message, status, details=None):
    return jsonify({"error": {"code": code, "message": message, "details": details or []}}), status


def _hash_password(raw_password):
    return bcrypt.hashpw(raw_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _doctor_json(doc):
    return {
        "id": doc.id,
        "user_id": doc.user_id,
        "email": doc.user.email if doc.user else None,
        "full_name": doc.full_name,
        "specialisation": doc.specialisation,
        "working_hours": doc.working_hours or {},
        "slot_duration_minutes": doc.slot_duration_minutes,
    }


@doctors_bp.get("/doctors/me")
@login_required
@role_required("doctor")
def doctor_me():
    """Chunk 3 proof route maintained for role-middleware compatibility."""
    doc = DoctorProfile.query.filter_by(user_id=g.current_user["id"]).first()
    return jsonify({
        "role": g.current_user["role"],
        "message": "Doctor-only route reached",
        "doctor": _doctor_json(doc) if doc else None,
    })


@doctors_bp.get("/doctors")
@login_required
def list_doctors():
    """List all doctors, optionally filtered by specialisation."""
    spec = request.args.get("specialisation", "").strip()
    query = DoctorProfile.query.join(User)
    if spec:
        query = query.filter(DoctorProfile.specialisation.ilike(f"%{spec}%"))
    doctors = query.order_by(DoctorProfile.full_name.asc()).all()
    return jsonify([_doctor_json(d) for d in doctors]), 200


@doctors_bp.get("/doctors/<int:doctor_id>")
@login_required
def get_doctor(doctor_id):
    """Retrieve details for a single doctor."""
    doc = DoctorProfile.query.get(doctor_id)
    if not doc:
        return _error("not_found", "Doctor profile not found", 404)
    return jsonify(_doctor_json(doc)), 200


@doctors_bp.post("/doctors")
@login_required
@role_required("admin")
def create_doctor():
    """Admin endpoint to create a new doctor profile and user account."""
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    full_name = (body.get("full_name") or "").strip()
    specialisation = (body.get("specialisation") or "").strip()
    working_hours = body.get("working_hours")
    if working_hours is None:
        working_hours = DEFAULT_WORKING_HOURS
    slot_duration = body.get("slot_duration_minutes", 20)

    details = []
    if not EMAIL_RE.match(email):
        details.append({"field": "email", "message": "Enter a valid email address"})
    if len(password) < 8:
        details.append({"field": "password", "message": "Password must be at least 8 characters"})
    if not full_name:
        details.append({"field": "full_name", "message": "Full name is required"})
    if not specialisation:
        details.append({"field": "specialisation", "message": "Specialisation is required"})
    if not isinstance(slot_duration, int) or slot_duration <= 0:
        details.append({"field": "slot_duration_minutes", "message": "Slot duration must be a positive integer"})

    if details:
        return _error("validation_error", "Check the highlighted fields", 422, details)

    if User.query.filter_by(email=email).first():
        return _error("email_taken", "An account with this email already exists", 409)

    user = User(email=email, password_hash=_hash_password(password), role="doctor")
    db.session.add(user)
    db.session.flush()

    doctor = DoctorProfile(
        user_id=user.id,
        full_name=full_name,
        specialisation=specialisation,
        working_hours=working_hours,
        slot_duration_minutes=slot_duration,
    )
    db.session.add(doctor)
    db.session.commit()

    return jsonify(_doctor_json(doctor)), 201


@doctors_bp.put("/doctors/<int:doctor_id>")
@login_required
@role_required("admin")
def update_doctor(doctor_id):
    """Admin endpoint to update doctor profile information."""
    doc = DoctorProfile.query.get(doctor_id)
    if not doc:
        return _error("not_found", "Doctor profile not found", 404)

    body = request.get_json(silent=True) or {}
    full_name = body.get("full_name")
    specialisation = body.get("specialisation")
    working_hours = body.get("working_hours")
    slot_duration = body.get("slot_duration_minutes")
    email = body.get("email")

    details = []
    if email is not None:
        email = email.strip().lower()
        if not EMAIL_RE.match(email):
            details.append({"field": "email", "message": "Enter a valid email address"})
        else:
            existing = User.query.filter(User.email == email, User.id != doc.user_id).first()
            if existing:
                return _error("email_taken", "An account with this email already exists", 409)
            doc.user.email = email

    if full_name is not None:
        full_name = full_name.strip()
        if not full_name:
            details.append({"field": "full_name", "message": "Full name cannot be empty"})
        else:
            doc.full_name = full_name

    if specialisation is not None:
        specialisation = specialisation.strip()
        if not specialisation:
            details.append({"field": "specialisation", "message": "Specialisation cannot be empty"})
        else:
            doc.specialisation = specialisation

    if working_hours is not None:
        if not isinstance(working_hours, dict):
            details.append({"field": "working_hours", "message": "Working hours must be an object"})
        else:
            doc.working_hours = working_hours

    if slot_duration is not None:
        if not isinstance(slot_duration, int) or slot_duration <= 0:
            details.append({"field": "slot_duration_minutes", "message": "Slot duration must be a positive integer"})
        else:
            doc.slot_duration_minutes = slot_duration

    if details:
        return _error("validation_error", "Check the highlighted fields", 422, details)

    db.session.commit()
    return jsonify(_doctor_json(doc)), 200


@doctors_bp.delete("/doctors/<int:doctor_id>")
@login_required
@role_required("admin")
def delete_doctor(doctor_id):
    """Admin endpoint to delete a doctor profile and associated user account."""
    doc = DoctorProfile.query.get(doctor_id)
    if not doc:
        return _error("not_found", "Doctor profile not found", 404)

    user = doc.user
    db.session.delete(doc)
    if user:
        db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "Doctor profile deleted successfully"}), 200
