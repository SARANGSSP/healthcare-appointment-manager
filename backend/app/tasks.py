"""
Celery task definitions (Build Plan Chunks 12–14 / Design Document §9).
H1  — LLM pre-visit and post-visit summaries run as async Celery tasks.
H3  — Notification retry/backoff runs as a periodic beat task.
H8  — Expired-hold sweep runs every 30 s as a periodic beat task.

Tasks use @shared_task so they bind automatically to whichever Celery
app is set as current (the one created in worker.py via create_celery).
Each task runs inside a Flask application context courtesy of the
ContextTask wrapper defined in celery_app.py::create_celery.
"""
from celery import shared_task


# ---------------------------------------------------------------------------
# H1: Async LLM pre-visit triage
# ---------------------------------------------------------------------------

@shared_task(bind=True, max_retries=3, default_retry_delay=30, name="tasks.run_pre_visit_llm")
def run_pre_visit_llm(self, appointment_id: int, symptoms_text: str):
    """
    Generates pre-visit urgency triage for *appointment_id* in the background.
    Updates SymptomSummary.llm_status to 'ok' or 'failed'.
    """
    from app.extensions import db
    from app.models import SymptomSummary, Appointment
    from app.services.llm import generate_pre_visit_summary

    try:
        appt = db.session.get(Appointment, appointment_id)
        if not appt:
            return {"status": "skipped", "reason": "appointment not found"}

        summary_dict = generate_pre_visit_summary(symptoms_text)

        ss = SymptomSummary.query.filter_by(appointment_id=appointment_id).first()
        if not ss:
            return {"status": "skipped", "reason": "symptom_summary row missing"}

        if summary_dict and "urgency" in summary_dict:
            ss.urgency = summary_dict.get("urgency", "Low")
            ss.chief_complaint = summary_dict.get("chief_complaint", symptoms_text[:120])
            ss.suggested_questions = summary_dict.get("suggested_questions", [])
            ss.llm_status = "ok"
        else:
            ss.llm_status = "failed"

        db.session.commit()
        return {"status": "ok", "appointment_id": appointment_id}

    except Exception as exc:
        raise self.retry(exc=exc)


# ---------------------------------------------------------------------------
# H1: Async LLM post-visit summary
# ---------------------------------------------------------------------------

@shared_task(bind=True, max_retries=3, default_retry_delay=30, name="tasks.run_post_visit_llm")
def run_post_visit_llm(self, appointment_id: int, clinical_notes: str, prescriptions: list):
    """
    Generates post-visit patient-friendly summary for *appointment_id* in the background.
    Updates VisitNote.patient_friendly_summary and VisitNote.llm_status.
    """
    from app.extensions import db
    from app.models import VisitNote
    from app.services.llm import generate_post_visit_summary

    try:
        vn = VisitNote.query.filter_by(appointment_id=appointment_id).first()
        if not vn:
            return {"status": "skipped", "reason": "visit_note row missing"}

        summary_dict = generate_post_visit_summary(clinical_notes, prescriptions)
        if summary_dict and "patient_summary" in summary_dict:
            vn.patient_friendly_summary = summary_dict["patient_summary"]
            vn.llm_status = "ok"
        else:
            vn.patient_friendly_summary = f"Patient Summary: {clinical_notes[:150]}"
            vn.llm_status = "failed"

        db.session.commit()
        return {"status": "ok", "appointment_id": appointment_id}

    except Exception as exc:
        raise self.retry(exc=exc)


# ---------------------------------------------------------------------------
# H3: Periodic notification retry with backoff
# ---------------------------------------------------------------------------

@shared_task(name="tasks.retry_notifications_task")
def retry_notifications_task():
    """
    Sweeps failed/pending notifications and retries with exponential backoff.
    Scheduled every 60 s by Celery beat (Design Document §9.1 retry schedule: 1 m/5 m/30 m).
    """
    from datetime import datetime, timezone, timedelta
    from app.extensions import db
    from app.models import Notification
    from app.services.notifications import send_notification

    now = datetime.now(timezone.utc)
    # Backoff windows per retry_count: 0→1 min, 1→5 min, 2→30 min, 3+→60 min
    BACKOFF_MINUTES = {0: 1, 1: 5, 2: 30}

    candidates = Notification.query.filter(
        Notification.status.in_(["failed", "pending"]),
        Notification.retry_count < 5,
    ).all()

    retried = 0
    for notif in candidates:
        wait_minutes = BACKOFF_MINUTES.get(notif.retry_count or 0, 60)
        if notif.last_attempt_at:
            last = notif.last_attempt_at
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            if (now - last).total_seconds() < wait_minutes * 60:
                continue
        send_notification(notif)
        retried += 1

    return {"retried": retried}


# ---------------------------------------------------------------------------
# H8: Periodic hold expiry sweep every 30 s
# ---------------------------------------------------------------------------

@shared_task(name="tasks.sweep_expired_holds_task")
def sweep_expired_holds_task():
    """
    Moves 'held' appointments older than 300 s to 'expired'.
    Scheduled every 30 s by Celery beat (Design Document §6.3).
    """
    from app.services.sweeper import sweep_expired_holds
    sweep_expired_holds()
    return {"status": "ok"}
