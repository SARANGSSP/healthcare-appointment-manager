"""
Medication Reminder Scheduler (Build Plan Chunk 14 / Design Document §9.1).
Creates MedicationReminder rows for each prescription item based on
the item's frequency string and duration_days.

H7 fix: this was never called from submit_visit_notes and frequency
was ignored — only duration_days was used.
"""
from datetime import datetime, timedelta, timezone

from app.extensions import db
from app.models import MedicationReminder

# Maps frequency strings (case-insensitive substrings) → doses per day
_FREQ_MAP = {
    "once": 1,
    "1x": 1,
    "1 time": 1,
    "twice": 2,
    "2x": 2,
    "2 time": 2,
    "three": 3,
    "3x": 3,
    "3 time": 3,
    "four": 4,
    "4x": 4,
    "4 time": 4,
    "daily": 1,        # default "daily" = 1 unless prefixed
    "every 8": 3,
    "every 6": 4,
    "every 12": 2,
}

# Base dose hours for N doses/day
_DOSE_HOURS = {
    1: [8],
    2: [8, 20],
    3: [8, 14, 20],
    4: [8, 12, 16, 20],
}


def _parse_doses_per_day(frequency_str: str) -> int:
    """Return number of doses per day from a free-text frequency string."""
    if not frequency_str:
        return 1
    lower = frequency_str.lower()
    for keyword, count in _FREQ_MAP.items():
        if keyword in lower:
            return count
    return 1  # safe default


def schedule_medication_reminders(visit_note) -> int:
    """
    Creates MedicationReminder rows for every PrescriptionItem in *visit_note*.

    Scheduling logic (Design Document §9.1):
    - Parse doses_per_day from item.frequency (H7 fix: was always ignored).
    - Schedule reminder rows starting tomorrow at appropriate hours,
      for item.duration_days days.
    - Existing reminders for the same item are left untouched (idempotent).

    Returns the total number of reminder rows created.
    """
    if not visit_note or not visit_note.prescription_items:
        return 0

    now_utc = datetime.now(timezone.utc)
    created = 0

    for item in visit_note.prescription_items:
        # Skip if reminders already exist for this item
        existing = MedicationReminder.query.filter_by(
            prescription_item_id=item.id
        ).count()
        if existing:
            continue

        doses_per_day = _parse_doses_per_day(item.frequency)
        dose_hours = _DOSE_HOURS.get(doses_per_day, [8])
        duration = max(int(item.duration_days or 1), 1)

        for day_offset in range(duration):
            target_date = now_utc.date() + timedelta(days=day_offset + 1)
            for hour in dose_hours:
                scheduled_for = datetime(
                    target_date.year, target_date.month, target_date.day,
                    hour, 0, 0, tzinfo=timezone.utc
                )
                reminder = MedicationReminder(
                    prescription_item_id=item.id,
                    scheduled_for=scheduled_for,
                    status="pending",
                )
                db.session.add(reminder)
                created += 1

    if created:
        db.session.commit()

    return created
