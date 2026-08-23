"""
Medication Reminders Scheduler (Build Plan Chunk 16).
Generates reminder schedules from prescription frequency.
"""
from datetime import datetime, timezone, timedelta

from app.extensions import db
from app.models import MedicationReminder, PrescriptionItem


def schedule_medication_reminders(prescription_item_id):
    """
    Schedules medication reminder entries based on prescription frequency and duration.
    """
    item = PrescriptionItem.query.get(prescription_item_id)
    if not item:
        return []

    duration_days = item.duration_days or 5
    now_utc = datetime.now(timezone.utc)

    reminders = []
    for day in range(duration_days):
        scheduled_time = now_utc + timedelta(days=day)
        reminder = MedicationReminder(
            prescription_item_id=item.id,
            scheduled_for=scheduled_time,
            status="pending"
        )
        db.session.add(reminder)
        reminders.append(reminder)

    db.session.commit()
    return reminders
