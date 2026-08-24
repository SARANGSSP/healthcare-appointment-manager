"""
Medication Reminders Scheduler (Build Plan Chunk 16 / Design Document §9.1).

H7 fix: Updated to parse the frequency field properly and accept a VisitNote object
        (which then schedules reminders for all prescription items at once).
        Backward-compat single-item signature retained for legacy callers.
"""
from datetime import datetime, timezone, timedelta

from app.extensions import db
from app.models import MedicationReminder, PrescriptionItem

# Maps frequency keywords → doses per day
_FREQ_MAP = {
    "once": 1, "1x": 1, "1 time": 1,
    "twice": 2, "2x": 2, "2 time": 2,
    "three": 3, "3x": 3, "3 time": 3,
    "four": 4, "4x": 4, "4 time": 4,
    "every 8": 3, "every 6": 4, "every 12": 2,
    "daily": 1,
}
_DOSE_HOURS = {1: [8], 2: [8, 20], 3: [8, 14, 20], 4: [8, 12, 16, 20]}


def _parse_doses_per_day(frequency_str: str) -> int:
    """Return number of doses per day from a free-text frequency string (H7 fix)."""
    if not frequency_str:
        return 1
    lower = frequency_str.lower()
    for keyword, count in _FREQ_MAP.items():
        if keyword in lower:
            return count
    return 1


def schedule_medication_reminders(target):
    """
    Schedules MedicationReminder rows for prescription items.

    Accepts either:
      - A VisitNote ORM object  → schedules reminders for all its PrescriptionItems (H7 new API)
      - An int prescription_item_id → schedules for that single item (backward compat)

    Returns the list of created MedicationReminder objects.
    """
    if isinstance(target, int):
        # Backward-compat path: single prescription_item_id
        return _schedule_for_item_id(target)

    # New path: VisitNote object
    visit_note = target
    if not visit_note or not visit_note.prescription_items:
        return []

    all_reminders = []
    for item in visit_note.prescription_items:
        all_reminders.extend(_schedule_for_item(item))

    return all_reminders


def _schedule_for_item_id(prescription_item_id: int):
    item = PrescriptionItem.query.get(prescription_item_id)
    if not item:
        return []
    return _schedule_for_item(item)


def _schedule_for_item(item: PrescriptionItem):
    """Create MedicationReminder rows for a single PrescriptionItem."""
    # Skip if already scheduled (idempotent)
    existing = MedicationReminder.query.filter_by(prescription_item_id=item.id).count()
    if existing:
        return []

    doses_per_day = _parse_doses_per_day(item.frequency)  # H7 fix: was always ignored
    dose_hours = _DOSE_HOURS.get(doses_per_day, [8])
    duration = max(int(item.duration_days or 1), 1)

    now_utc = datetime.now(timezone.utc)
    reminders = []
    for day_offset in range(duration):
        target_date = now_utc.date() + timedelta(days=day_offset + 1)
        for hour in dose_hours:
            scheduled_time = datetime(
                target_date.year, target_date.month, target_date.day,
                hour, 0, 0, tzinfo=timezone.utc
            )
            reminder = MedicationReminder(
                prescription_item_id=item.id,
                scheduled_for=scheduled_time,
                status="pending"
            )
            db.session.add(reminder)
            reminders.append(reminder)

    if reminders:
        db.session.commit()
    return reminders
