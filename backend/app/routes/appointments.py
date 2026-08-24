"""
Appointments blueprint (Build Plan Chunks 8–13 / Design Document §6–§10).
Handles slot holds (~300s TTL), double-booking prevention, cancellation, visit notes,
LLM pre-visit & post-visit summaries, and doctor queue management.

Bug fixes applied in this version:
  C2  — confirm_booking now checks patient ownership before confirming.
  C3  — submit_visit_notes now checks doctor ownership before accepting notes.
  C4  — hold_status and get_appointment_summary now enforce ownership.
  M2  — Admin hold requires explicit patient_id in body (no more .first() fallback).
  M3  — submit_visit_notes rejects appointments not in 'confirmed' status.
  M5  — New GET /appointments/mine endpoint for patient's own appointments.
  H4  — confirm_booking and cancel_appointment now wire enqueue_notification
        and sync_calendar_event on every state change.
  H7  — submit_visit_notes calls schedule_medication_reminders after commit.
  H1  — LLM calls dispatched as async Celery tasks (run_pre_visit_llm,
        run_post_visit_llm) so the request returns immediately with
        llm_status='pending'; the task updates it to 'ok'/'failed'.
"""
from datetime import datetime, time, timedelta, timezone
import re

from flask import Blueprint, g, jsonify, request
from sqlalchemy.exc import IntegrityError

from app.auth.decorators import login_required, role_required
from app.config import Config
from app.extensions import db
from app.models import Appointment, DoctorLeave, DoctorProfile, PatientProfile, PrescriptionItem, SymptomSummary, User, VisitNote, Notification

from app.services.locks import acquire_slot_lock
from app.services.sweeper import sweep_expired_holds

appointments_bp = Blueprint("appointments", __name__)

HOLD_TTL_SECONDS = 300


def _error(code, message, status, details=None):
    return jsonify({"error": {"code": code, "message": message, "details": details or []}}), status


def _get_patient_profile(user_id):
    return PatientProfile.query.filter_by(user_id=user_id).first()


def _get_doctor_profile(user_id):
    return DoctorProfile.query.filter_by(user_id=user_id).first()


# Keep local alias so existing call-sites inside this module still work.
def _sweep_expired_holds():
    sweep_expired_holds()


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

    symptom_data = None
    if appt.symptom_summary:
        ss = appt.symptom_summary
        symptom_data = {
            "raw_symptoms": ss.raw_symptoms,
            "urgency": ss.urgency or "Low",
            "chief_complaint": ss.chief_complaint or ss.raw_symptoms,
            "suggested_questions": ss.suggested_questions or [],
            "llm_status": ss.llm_status or "pending",
        }

    visit_note_data = None
    if appt.visit_note:
        vn = appt.visit_note
        prescriptions = [
            {
                "id": item.id,
                "medication_name": item.medication_name,
                "dosage": item.dosage,
                "frequency": item.frequency,
                "duration_days": item.duration_days,
            }
            for item in (vn.prescription_items or [])
        ]
        visit_note_data = {
            "clinical_notes": vn.clinical_notes,
            "patient_friendly_summary": vn.patient_friendly_summary,
            "llm_status": vn.llm_status or "pending",
            "prescriptions": prescriptions,
        }

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
        "symptoms": ss.raw_symptoms if appt.symptom_summary and (ss := appt.symptom_summary) else None,
        "symptom_summary": symptom_data,
        "visit_note": visit_note_data,
    }


def _is_appointment_owner(appt, user_id, user_role):
    """Returns True if the current user owns this appointment (as patient or doctor) or is admin."""
    if user_role == "admin":
        return True
    is_patient_owner = appt.patient and appt.patient.user_id == user_id
    is_doctor_owner = appt.doctor and appt.doctor.user_id == user_id
    return bool(is_patient_owner or is_doctor_owner)


@appointments_bp.get("/appointments/today")
@login_required
@role_required("doctor")
def doctor_today_queue():
    """
    GET /appointments/today (Chunk 12)
    Doctor today's queue ordered by time with urgency badges and symptom summary.
    """
    _sweep_expired_holds()
    doc = _get_doctor_profile(g.current_user["id"])
    if not doc:
        return _error("not_found", "Doctor profile not found for this account", 404)

    today = datetime.now().date()
    date_param = request.args.get("date", "").strip()
    if date_param:
        try:
            today = datetime.strptime(date_param, "%Y-%m-%d").date()
        except ValueError:
            pass

    appts = Appointment.query.filter(
        Appointment.doctor_id == doc.id,
        Appointment.appt_date == today,
        Appointment.status.in_(["confirmed", "completed", "held"])
    ).order_by(Appointment.slot_start.asc()).all()

    return jsonify([_appointment_json(a) for a in appts]), 200


# ---------------------------------------------------------------------------
# M5: GET /appointments/mine — returns the calling patient's appointments
# ---------------------------------------------------------------------------

@appointments_bp.get("/appointments/mine")
@login_required
def my_appointments():
    """
    GET /appointments/mine (M5 fix)
    Returns all appointments for the currently authenticated patient,
    ordered by date descending. Patients see their own; doctors/admins
    get a 403.
    """
    user_role = g.current_user["role"]
    user_id = g.current_user["id"]

    if user_role != "patient":
        return _error("forbidden", "This endpoint is for patients only", 403)

    patient = _get_patient_profile(user_id)
    if not patient:
        return _error("not_found", "Patient profile not found", 404)

    appts = Appointment.query.filter_by(patient_id=patient.id).order_by(
        Appointment.appt_date.desc(), Appointment.slot_start.desc()
    ).all()

    return jsonify([_appointment_json(a) for a in appts]), 200


@appointments_bp.post("/appointments/hold")
@login_required
def hold_slot():
    """POST /appointments/hold (Chunk 8)"""
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

    leave = DoctorLeave.query.filter_by(doctor_id=doctor_id, leave_date=target_date).first()
    if leave:
        return _error("doctor_on_leave", "Doctor is on leave on this date", 409)

    if not acquire_slot_lock(doctor_id, date_str, slot_start_str, request_id=str(user_id)):
        return _error("slot_taken", "This slot is no longer available. Please select another slot.", 409)

    existing_active = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.appt_date == target_date,
        Appointment.slot_start == start_time,
        Appointment.status.in_(["held", "confirmed"])
    ).first()

    if existing_active:
        return _error("slot_taken", "This slot is no longer available. Please select another slot.", 409)

    # M2 fix: admin must supply patient_id explicitly — no more PatientProfile.query.first() fallback.
    if not patient and user_role == "admin":
        admin_patient_id = body.get("patient_id")
        if not admin_patient_id:
            return _error(
                "validation_error",
                "Admins must supply 'patient_id' when holding a slot on behalf of a patient",
                422,
                [{"field": "patient_id", "message": "patient_id is required for admin-initiated holds"}]
            )
        patient = PatientProfile.query.get(admin_patient_id)
        if not patient:
            return _error("not_found", f"Patient profile {admin_patient_id} not found", 404)

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
    """
    GET /appointments/{id}/hold-status
    C4 fix: caller must own the appointment (or be admin).
    """
    _sweep_expired_holds()
    appt = Appointment.query.get(appointment_id)
    if not appt:
        return _error("not_found", "Appointment not found", 404)

    # C4 fix: ownership check — patients and doctors can only see their own
    if not _is_appointment_owner(appt, g.current_user["id"], g.current_user["role"]):
        return _error("forbidden", "You are not authorized to view this appointment", 403)

    return jsonify(_appointment_json(appt)), 200


@appointments_bp.post("/appointments/<int:appointment_id>/confirm")
@login_required
def confirm_booking(appointment_id):
    """
    POST /appointments/{id}/confirm (Chunk 9 + Chunk 12 Pre-visit LLM Triage)
    C2 fix: only the owning patient (or admin) may confirm.
    H4 fix: enqueue_notification and sync_calendar_event called after confirm.
    H1 fix: LLM call dispatched as async Celery task (returns pending status immediately).
    """
    _sweep_expired_holds()
    appt = Appointment.query.get(appointment_id)
    if not appt:
        return _error("not_found", "Appointment not found", 404)

    # C2 fix: only the patient who holds it (or an admin) may confirm
    user_role = g.current_user["role"]
    user_id = g.current_user["id"]
    if user_role != "admin":
        if not (appt.patient and appt.patient.user_id == user_id):
            return _error("forbidden", "You are not authorized to confirm this appointment", 403)

    if appt.status == "expired":
        return _error("hold_expired", "Slot hold has expired. Please select the slot again.", 409)
    if appt.status == "confirmed":
        return jsonify(_appointment_json(appt)), 200
    if appt.status != "held":
        return _error("invalid_status", f"Cannot confirm appointment in status '{appt.status}'", 400)

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
            # H1 fix: create SymptomSummary with llm_status="pending" immediately,
            # then fire async task to fill in the real LLM result.
            ss = SymptomSummary(
                appointment_id=appt.id,
                raw_symptoms=symptoms_text,
                urgency="Low",
                chief_complaint=symptoms_text[:120],
                suggested_questions=[],
                llm_status="pending",
            )
            db.session.add(ss)

        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return _error("slot_taken", "This slot is no longer available. Please select another slot.", 409)

    # H1: dispatch LLM triage as async task (after commit so the SS row exists)
    if symptoms_text:
        try:
            from app.tasks import run_pre_visit_llm
            run_pre_visit_llm.delay(appt.id, symptoms_text)
        except Exception:
            # Celery may not be running in dev/test; graceful fallback
            pass

    # H4 fix: wire notification and calendar sync
    try:
        from app.services.notifications import enqueue_notification
        recipient_email = appt.patient.user.email if appt.patient and appt.patient.user else ""
        enqueue_notification(appt.id, "confirmation", recipient=recipient_email)
    except Exception:
        pass  # notification failure must not block the booking response

    try:
        from app.services.calendar import sync_calendar_event
        sync_calendar_event(appt.id, action="create")
    except Exception:
        pass  # calendar sync failure must not block the booking response

    return jsonify(_appointment_json(appt)), 200


@appointments_bp.post("/appointments/<int:appointment_id>/visit-notes")
@login_required
@role_required("doctor", "admin")
def submit_visit_notes(appointment_id):
    """
    POST /appointments/{id}/visit-notes (Chunk 13)
    Doctor submits clinical notes + prescriptions → triggers post-visit LLM summary.
    C3  fix: only the appointment's doctor (or admin) may submit notes.
    M3  fix: appointment must be in 'confirmed' status.
    H7  fix: schedule_medication_reminders() called after commit.
    H1  fix: LLM post-visit summary dispatched as async task.
    """
    appt = Appointment.query.get(appointment_id)
    if not appt:
        return _error("not_found", "Appointment not found", 404)

    user_role = g.current_user["role"]
    user_id = g.current_user["id"]

    # C3 fix: doctor must own this appointment
    if user_role != "admin":
        doc = _get_doctor_profile(user_id)
        if not doc or doc.id != appt.doctor_id:
            return _error("forbidden", "You can only submit notes for your own appointments", 403)

    # M3 fix: guard against notes on un-confirmed appointments
    if appt.status != "confirmed":
        return _error(
            "invalid_status",
            f"Visit notes can only be submitted for confirmed appointments (current status: '{appt.status}')",
            400
        )

    body = request.get_json(silent=True) or {}
    clinical_notes = (body.get("clinical_notes") or "").strip()
    prescriptions_input = body.get("prescriptions") or []

    if not clinical_notes:
        return _error("validation_error", "Check the highlighted fields", 422, [
            {"field": "clinical_notes", "message": "Clinical notes are required"}
        ])

    # 1. Create or update VisitNote — llm_status starts as "pending" (H1 fix)
    vn = appt.visit_note
    if not vn:
        vn = VisitNote(appointment_id=appt.id, clinical_notes=clinical_notes, llm_status="pending")
        db.session.add(vn)
        db.session.flush()
    else:
        vn.clinical_notes = clinical_notes
        vn.llm_status = "pending"

    # 2. Add Prescription items
    if isinstance(prescriptions_input, list):
        for item in prescriptions_input:
            med_name = (item.get("medication_name") or "").strip()
            if med_name:
                p_item = PrescriptionItem(
                    visit_note_id=vn.id,
                    medication_name=med_name,
                    dosage=item.get("dosage", "1 tablet"),
                    frequency=item.get("frequency", "daily"),
                    duration_days=int(item.get("duration_days", 5))
                )
                db.session.add(p_item)

    appt.status = "completed"
    db.session.commit()

    # H1 fix: dispatch async post-visit LLM task
    try:
        from app.tasks import run_post_visit_llm
        run_post_visit_llm.delay(appt.id, clinical_notes, prescriptions_input)
    except Exception:
        pass  # Celery may not be running in dev/test

    # H7 fix: schedule medication reminders from prescription items
    try:
        from app.services.reminders import schedule_medication_reminders
        # Re-query vn to include the freshly-committed prescription_items
        vn = VisitNote.query.get(vn.id)
        schedule_medication_reminders(vn)
    except Exception:
        pass  # reminder scheduling must not block the visit-notes response

    return jsonify(_appointment_json(appt)), 200


@appointments_bp.get("/appointments/<int:appointment_id>/summary")
@login_required
def get_appointment_summary(appointment_id):
    """
    GET /appointments/{id}/summary (Chunks 12 & 13)
    C4 fix: caller must own the appointment (or be admin).
    H5: this endpoint is now surfaced in the patient frontend.
    """
    appt = Appointment.query.get(appointment_id)
    if not appt:
        return _error("not_found", "Appointment not found", 404)

    # C4 fix: ownership check
    if not _is_appointment_owner(appt, g.current_user["id"], g.current_user["role"]):
        return _error("forbidden", "You are not authorized to view this appointment summary", 403)

    return jsonify(_appointment_json(appt)), 200


@appointments_bp.delete("/appointments/<int:appointment_id>")
@login_required
def cancel_appointment(appointment_id):
    """
    DELETE /appointments/{id} (Chunk 10)
    H4 fix: enqueue_notification called when appointment is cancelled.
    """
    appt = Appointment.query.get(appointment_id)
    if not appt:
        return _error("not_found", "Appointment not found", 404)

    user_role = g.current_user["role"]
    user_id = g.current_user["id"]

    is_patient_owner = appt.patient and appt.patient.user_id == user_id
    is_doctor_owner = appt.doctor and appt.doctor.user_id == user_id

    if user_role != "admin" and not is_patient_owner and not is_doctor_owner:
        return _error("forbidden", "You are not authorized to cancel this appointment", 403)

    if appt.status in ("cancelled", "leave_cancelled", "expired"):
        return jsonify({"message": f"Appointment is already {appt.status}", "appointment": _appointment_json(appt)}), 200

    appt.status = "cancelled"
    db.session.commit()

    # Release the Redis slot lock (B9)
    try:
        from app.services.locks import release_slot_lock
        release_slot_lock(appt.doctor_id, appt.appt_date.strftime("%Y-%m-%d"), appt.slot_start.strftime("%H:%M"))
    except Exception:
        pass

    # B4 fix: Delete calendar event
    try:
        from app.services.calendar import sync_calendar_event
        sync_calendar_event(appt.id, action="delete")
    except Exception:
        pass

    # H4 fix: notify patient of cancellation (B2 aligned)
    try:
        from app.services.notifications import enqueue_notification
        recipient_email = appt.patient.user.email if appt.patient and appt.patient.user else ""
        enqueue_notification(appt.id, "cancellation", recipient=recipient_email)
    except Exception:
        pass

    return jsonify({"message": "Appointment cancelled successfully", "appointment": _appointment_json(appt)}), 200
