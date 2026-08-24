"""
Shared hold-expiry sweeper (Build Plan Chunk 8 / Design Document §6.3).
Extracted from appointments.py so it can be called from both the
appointments blueprint and the doctors availability route without
creating a circular import.

H8 fix: _sweep_expired_holds was missing from doctor_availability route.
"""
from datetime import datetime, timezone

from app.extensions import db
from app.models import Appointment

HOLD_TTL_SECONDS = 300


def sweep_expired_holds():
    """
    Flips any 'held' appointment older than HOLD_TTL_SECONDS (300 s) to 'expired'.
    Safe to call from any Flask request context.
    """
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
