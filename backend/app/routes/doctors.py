"""
Doctor & Admin Profile Management endpoints (Build Plan Chunk 5 / Design Document §5).
Admin CRUD operations for Doctor profiles + doctor search for patients.
"""
import re
from datetime import datetime, time, timedelta

import bcrypt
from flask import Blueprint, g, jsonify, request

from app.auth.decorators import login_required, role_required
from app.extensions import db
from app.models import Appointment, DoctorLeave, DoctorProfile, User


doctors_bp = Blueprint("doctors", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

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


def _generate_slots(working_windows, duration_minutes):
    """Slices working time windows into slot intervals."""
    slots = []
    if not working_windows or not isinstance(working_windows, list):
        return slots

    for window in working_windows:
        if not isinstance(window, str) or "-" not in window:
            continue
        parts = window.split("-")
        try:
            start_dt = datetime.strptime(parts[0].strip(), "%H:%M")
            end_dt = datetime.strptime(parts[1].strip(), "%H:%M")
        except ValueError:
            continue

        delta = timedelta(minutes=duration_minutes)
        curr = start_dt
        while curr + delta <= end_dt:
            slot_start_str = curr.strftime("%H:%M")
            slot_end_str = (curr + delta).strftime("%H:%M")
            slots.append((slot_start_str, slot_end_str))
            curr += delta

    return slots


@doctors_bp.get("/doctors/<int:doctor_id>/availability")
@login_required
def doctor_availability(doctor_id):
    """
    Computes real slot availability for a doctor on a specific date:
    (Working hours - Leave - Existing active bookings)
    """
    doc = DoctorProfile.query.get(doctor_id)
    if not doc:
        return _error("not_found", "Doctor profile not found", 404)

    date_str = (request.args.get("date") or "").strip()
    if not date_str:
        target_date = datetime.now().date()
        date_str = target_date.isoformat()
    else:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return _error("validation_error", "Check the highlighted fields", 422, [
                {"field": "date", "message": "Date must be in YYYY-MM-DD format"}
            ])

    weekday_name = WEEKDAYS[target_date.weekday()]

    # 1. Check if doctor is on leave
    leave = DoctorLeave.query.filter_by(doctor_id=doctor_id, leave_date=target_date).first()
    if leave:
        return jsonify({
            "doctor_id": doc.id,
            "date": date_str,
            "weekday": weekday_name,
            "on_leave": True,
            "leave_reason": leave.reason,
            "slot_duration_minutes": doc.slot_duration_minutes,
            "slots": []
        }), 200

    # 2. Get working hours for the weekday
    working_hours = doc.working_hours or DEFAULT_WORKING_HOURS
    windows = working_hours.get(weekday_name, [])
    if not windows and weekday_name in ("mon", "tue", "wed", "thu", "fri"):
        windows = DEFAULT_WORKING_HOURS.get(weekday_name, [])

    raw_slots = _generate_slots(windows, doc.slot_duration_minutes)

    # 3. Query existing active appointments for this doctor & date
    active_appts = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.appt_date == target_date,
        Appointment.status.in_(["held", "confirmed"])
    ).all()

    taken_starts = {appt.slot_start.strftime("%H:%M") for appt in active_appts}

    slot_list = []
    for start_s, end_s in raw_slots:
        is_taken = start_s in taken_starts
        slot_list.append({
            "start_time": start_s,
            "end_time": end_s,
            "status": "taken" if is_taken else "available"
        })

    return jsonify({
        "doctor_id": doc.id,
        "date": date_str,
        "weekday": weekday_name,
        "on_leave": False,
        "leave_reason": None,
        "slot_duration_minutes": doc.slot_duration_minutes,
        "slots": slot_list
    }), 200


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


def _leave_json(leave):
    return {
        "id": leave.id,
        "doctor_id": leave.doctor_id,
        "leave_date": leave.leave_date.isoformat(),
        "reason": leave.reason,
    }


@doctors_bp.get("/doctors/<int:doctor_id>/leave")
@login_required
def list_doctor_leave(doctor_id):
    """Retrieve all leave dates for a doctor."""
    doc = DoctorProfile.query.get(doctor_id)
    if not doc:
        return _error("not_found", "Doctor profile not found", 404)
    leaves = DoctorLeave.query.filter_by(doctor_id=doctor_id).order_by(DoctorLeave.leave_date.asc()).all()
    return jsonify([_leave_json(l) for l in leaves]), 200


@doctors_bp.post("/doctors/<int:doctor_id>/leave")
@login_required
def mark_doctor_leave(doctor_id):
    """Mark a leave date for a doctor (admin or doctor themselves)."""
    doc = DoctorProfile.query.get(doctor_id)
    if not doc:
        return _error("not_found", "Doctor profile not found", 404)

    current_role = g.current_user["role"]
    current_user_id = g.current_user["id"]
    if current_role != "admin" and doc.user_id != current_user_id:
        return _error("forbidden", "You are not authorized to mark leave for this doctor", 403)

    body = request.get_json(silent=True) or {}
    leave_date_str = (body.get("leave_date") or "").strip()
    reason = (body.get("reason") or "").strip() or None

    if not leave_date_str:
        return _error("validation_error", "Check the highlighted fields", 422, [
            {"field": "leave_date", "message": "Leave date is required"}
        ])

    try:
        leave_date = datetime.strptime(leave_date_str, "%Y-%m-%d").date()
    except ValueError:
        return _error("validation_error", "Check the highlighted fields", 422, [
            {"field": "leave_date", "message": "Leave date must be in YYYY-MM-DD format"}
        ])

    existing = DoctorLeave.query.filter_by(doctor_id=doctor_id, leave_date=leave_date).first()
    if existing:
        return _error("leave_exists", "Doctor is already marked on leave for this date", 409)

    # Design Document §8: Lock active appointments for this doctor & date FOR UPDATE
    # to prevent double-booking race during leave marking
    try:
        active_appts = Appointment.query.filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appt_date == leave_date,
            Appointment.status.in_(["held", "confirmed"])
        ).with_for_update().all()
    except Exception:
        # Fallback if DB engine doesn't support with_for_update (e.g. SQLite test)
        active_appts = Appointment.query.filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appt_date == leave_date,
            Appointment.status.in_(["held", "confirmed"])
        ).all()

    affected_count = len(active_appts)
    for appt in active_appts:
        appt.status = "leave_cancelled"

    leave = DoctorLeave(doctor_id=doctor_id, leave_date=leave_date, reason=reason)
    db.session.add(leave)
    db.session.commit()

    res_data = _leave_json(leave)
    res_data["affected_appointments_count"] = affected_count
    return jsonify(res_data), 201



@doctors_bp.delete("/doctors/<int:doctor_id>/leave/<int:leave_id>")
@login_required
def delete_doctor_leave(doctor_id, leave_id):
    """Remove a marked leave date."""
    doc = DoctorProfile.query.get(doctor_id)
    if not doc:
        return _error("not_found", "Doctor profile not found", 404)

    current_role = g.current_user["role"]
    current_user_id = g.current_user["id"]
    if current_role != "admin" and doc.user_id != current_user_id:
        return _error("forbidden", "You are not authorized to modify leave for this doctor", 403)

    leave = DoctorLeave.query.filter_by(id=leave_id, doctor_id=doctor_id).first()
    if not leave:
        return _error("not_found", "Leave record not found", 404)

    db.session.delete(leave)
    db.session.commit()

    return jsonify({"message": "Leave date removed successfully"}), 200

