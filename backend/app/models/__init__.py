"""
Importing every model here (rather than relying on each route module
to import what it needs) guarantees Alembic's autogenerate sees the
full schema regardless of which blueprints are registered yet.
"""
from app.models.user import User
from app.models.patient_profile import PatientProfile
from app.models.doctor_profile import DoctorProfile
from app.models.doctor_leave import DoctorLeave
from app.models.appointment import Appointment
from app.models.symptom_summary import SymptomSummary
from app.models.visit_note import VisitNote
from app.models.prescription_item import PrescriptionItem
from app.models.medication_reminder import MedicationReminder
from app.models.notification import Notification
from app.models.calendar_event import CalendarEvent

__all__ = [
    "User",
    "PatientProfile",
    "DoctorProfile",
    "DoctorLeave",
    "Appointment",
    "SymptomSummary",
    "VisitNote",
    "PrescriptionItem",
    "MedicationReminder",
    "Notification",
    "CalendarEvent",
]
