"""
Appointments blueprint (Build Plan Chunks 8 & 9 / Design Document §6, §7).
Handles short-lived slot holds (~300s TTL), stale hold sweeping, double-booking prevention
via PostgreSQL partial unique index, and booking confirmation with symptom submission.
"""
from datetime import datetime, time, timedelta, timezone
import re

from flask import Blueprint, g, jsonify, request
from sqlalchemy.exc import IntegrityError

from app.auth.decorators import login_required, role_required
from app.config import Config
from app.extensions import db
from app.models import Appointment, DoctorLeave, DoctorProfile, PatientProfile, SymptomSummary, User

appointments_bp = Blueprint("appointments", __name__)

HOLD_TTL_SECONDS = 300


def _error(code, message, status, details=None):
    return jsonify({"error": {"code": code, "message": message, "details": details or []}}), status


def _get_patient_profile(user_id):
    return PatientProfile.query.filter_by(user_id=user_id).first()


def _sweep_expired_holds():
    """Flips any 'held' appointment older than 300 seconds to 'expired'."""
    now_utc = datetime.now(timezone.utc)
    held_appts = Appointment.query.filter_by(status="held").all()
    updated = False
    for appt in held_appts:
        held_at_utc = _make_utc(appt.held_at)
        if held_at_utc and (now_utc - held_at_utc).total_seconds() > HOLD_TTL_SECONDS:
            appt.status = "expired"
            updated = True
    if updated:
        db.session.commit()



def _make_utc(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _appointment_json(appt):
    patient_name = appt.patient.full_name if appt.patient else "Patient"
    doctor_name = appt.doctor.full_name if appt.doctor else "Doctor"
    specialisation = appt.doctor.specialisation if appt.doctor else ""

    held_at_utc = _make_utc(appt.held_at)
    confirmed_at_utc = _make_utc(appt.confirmed_at)

    held_at_iso = held_at_utc.isoformat() if held_at_utc else None
    confirmed_at_iso = confirmed_at_utc.isoformat() if confirmed_at_utc else None

    # Calculate remaining TTL for held slots
    ttl = 0
    if appt.status == "held" and held_at_utc:
        now_utc = datetime.now(timezone.utc)
        elapsed = (now_utc - held_at_utc).total_seconds()
        ttl = max(0, int(HOLD_TTL_SECONDS - elapsed))


    return {
        "id": appt.id,
        "patient_id": appt.patient_id,
        "patient_name": patient_name,
        "doctor_id": appt.doctor_id,
        "doctor_name": doctor_name,
        "specialisation": specialisation,
        "appt_date": appt.appt_date.isoformat(),
        "slot_start": appt.slot_start.strftime("%H:%M"),
        "slot_end": appt.slot_end.strftime("%H:%M"),
        "status": appt.status,
        "held_at": held_at_iso,
        "confirmed_at": confirmed_at_iso,
        "ttl_seconds": ttl,
        "symptoms": appt.symptom_summary.raw_symptoms if appt.symptom_summary else None,
    }


@appointments_bp.post("/appointments/hold")
@login_required
def hold_slot():
    """
    POST /appointments/hold (Chunk 8)
    Acquires short-lived hold on a slot (~300s TTL) and inserts 'held' appointment row.
    Guarded by partial unique index idx_appt_no_double_book (Design Document §6, §7).
    """
    _sweep_expired_holds()

    user_role = g.current_user["role"]
    user_id = g.current_user["id"]

    patient = _get_patient_profile(user_id)
    if not patient and user_role != "admin":
        return _error("forbidden", "Only patients or admins can hold appointment slots", 403)

    body = request.get_json(silent=True) or {}
    doctor_id = body.get("doctor_id")
    date_str = (body.get("appt_date") or "").strip()
    slot_start_str = (body.get("slot_start") or "").strip()
    slot_end_str = (body.get("slot_end") or "").strip()

    details = []
    if not doctor_id or not isinstance(doctor_id, int):
        details.append({"field": "doctor_id", "message": "Valid doctor ID is required"})
    if not date_str:
        details.append({"field": "appt_date", "message": "Appointment date (YYYY-MM-DD) is required"})
    if not slot_start_str:
        details.append({"field": "slot_start", "message": "Slot start time (HH:MM) is required"})
    if not slot_end_str:
        details.append({"field": "slot_end", "message": "Slot end time (HH:MM) is required"})

    if details:
        return _error("validation_error", "Check the highlighted fields", 422, details)

    doctor = DoctorProfile.query.get(doctor_id)
    if not doctor:
        return _error("not_found", "Doctor profile not found", 404)

    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return _error("validation_error", "Check the highlighted fields", 422, [
            {"field": "appt_date", "message": "Invalid date format, expected YYYY-MM-DD"}
        ])

    try:
        start_time = datetime.strptime(slot_start_str, "%H:%M").time()
        end_time = datetime.strptime(slot_end_str, "%H:%M").time()
    except ValueError:
        return _error("validation_error", "Check the highlighted fields", 422, [
            {"field": "slot_time", "message": "Invalid time format, expected HH:MM"}
        ])

    # Check if doctor is on leave on target date
    leave = DoctorLeave.query.filter_by(doctor_id=doctor_id, leave_date=target_date).first()
    if leave:
        return _error("doctor_on_leave", "Doctor is on leave on this date", 409)

    # Check if slot is already actively held or confirmed in DB
    existing_active = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.appt_date == target_date,
        Appointment.slot_start == start_time,
        Appointment.status.in_(["held", "confirmed"])
    ).first()

    if existing_active:
        return _error("slot_taken", "This slot is no longer available. Please select another slot.", 409)

    # Use first available patient_profile if admin is testing hold
    if not patient and user_role == "admin":
        patient = PatientProfile.query.first()
        if not patient:
            return _error("no_patient", "No patient profile found in system", 400)

    try:
        appt = Appointment(
            patient_id=patient.id,
            doctor_id=doctor_id,
            appt_date=target_date,
            slot_start=start_time,
            slot_end=end_time,
            status="held",
            held_at=datetime.now(timezone.utc),
        )
        db.session.add(appt)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("slot_taken", "This slot is no longer available. Please select another slot.", 409)

    return jsonify(_appointment_json(appt)), 201


@appointments_bp.get("/appointments/<int:appointment_id>/hold-status")
@login_required
def hold_status(appointment_id):
    """GET /appointments/{id}/hold-status — checks remaining TTL for a slot hold."""
    _sweep_expired_holds()
    appt = Appointment.query.get(appointment_id)
    if not appt:
        return _error("not_found", "Appointment not found", 404)

    return jsonify(_appointment_json(appt)), 200


@appointments_bp.post("/appointments/<int:appointment_id>/confirm")
@login_required
def confirm_booking(appointment_id):
    """
    POST /appointments/{id}/confirm (Chunk 9)
    Confirms a held slot after symptom submission.
    Guarded by status check, 300s TTL check, and DB partial unique index constraint.
    """
    _sweep_expired_holds()
    appt = Appointment.query.get(appointment_id)
    if not appt:
        return _error("not_found", "Appointment not found", 404)

    # Check status
    if appt.status == "expired":
        return _error("hold_expired", "Slot hold has expired. Please select the slot again.", 409)
    if appt.status == "confirmed":
        return jsonify(_appointment_json(appt)), 200
    if appt.status != "held":
        return _error("invalid_status", f"Cannot confirm appointment in status '{appt.status}'", 400)

    # Check TTL explicitly (300 seconds)
    if appt.held_at:
        now_utc = datetime.now(timezone.utc)
        elapsed = (now_utc - _make_utc(appt.held_at)).total_seconds()
        if elapsed > HOLD_TTL_SECONDS:
            appt.status = "expired"
            db.session.commit()
            return _error("hold_expired", "Slot hold has expired. Please select the slot again.", 409)


    body = request.get_json(silent=True) or {}
    symptoms_text = (body.get("symptoms") or "").strip()

    try:
        appt.status = "confirmed"
        appt.confirmed_at = datetime.now(timezone.utc)

        if symptoms_text:
            if appt.symptom_summary:
                appt.symptom_summary.raw_symptoms = symptoms_text
            else:
                db.session.add(
                    SymptomSummary(
                        appointment_id=appt.id,
                        raw_symptoms=symptoms_text,
                        llm_status="pending"
                    )
                )

        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("slot_taken", "This slot is no longer available. Please select another slot.", 409)

    return jsonify(_appointment_json(appt)), 200
