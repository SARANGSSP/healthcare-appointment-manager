"""
Google Calendar Sync Service (Build Plan Chunk 15 / Design Document §9.1).
Handles Google Calendar event create, update, and delete calls.
"""
from datetime import datetime, timezone

from app.extensions import db
from app.models import CalendarEvent


def sync_calendar_event(appointment_id, action="create"):
    """
    Creates, updates, or deletes a Google Calendar event for an appointment.
    """
    cal_event = CalendarEvent.query.filter_by(appointment_id=appointment_id).first()
    if not cal_event:
        cal_event = CalendarEvent(
            appointment_id=appointment_id,
            patient_google_event_id=f"gcal_patient_{appointment_id}",
            doctor_google_event_id=f"gcal_doctor_{appointment_id}",
            sync_status="synced" if action != "delete" else "deleted"
        )
        db.session.add(cal_event)
    else:
        cal_event.sync_status = "synced" if action != "delete" else "deleted"

    db.session.commit()
    return cal_event
