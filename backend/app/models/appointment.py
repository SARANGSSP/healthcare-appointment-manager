from datetime import datetime, timezone

from app.extensions import db


class Appointment(db.Model):
    """
    Design Document §6: the partial unique index below (filtered to
    'held'/'confirmed') is the actual double-booking guard — the
    Redis hold in Chunk 8 is a UX-layer convenience on top of it,
    never a substitute for it.
    """

    __tablename__ = "appointment"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(
        db.Integer, db.ForeignKey("patient_profile.id", ondelete="CASCADE"), nullable=False
    )
    doctor_id = db.Column(
        db.Integer, db.ForeignKey("doctor_profile.id", ondelete="CASCADE"), nullable=False
    )
    appt_date = db.Column(db.Date, nullable=False)
    slot_start = db.Column(db.Time, nullable=False)
    slot_end = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="held")
    held_at = db.Column(db.DateTime(timezone=True))
    confirmed_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    patient = db.relationship("PatientProfile", back_populates="appointments")
    doctor = db.relationship("DoctorProfile", back_populates="appointments")
    symptom_summary = db.relationship(
        "SymptomSummary", back_populates="appointment", uselist=False, cascade="all, delete-orphan"
    )
    visit_note = db.relationship(
        "VisitNote", back_populates="appointment", uselist=False, cascade="all, delete-orphan"
    )
    notifications = db.relationship(
        "Notification", back_populates="appointment", cascade="all, delete-orphan"
    )
    calendar_event = db.relationship(
        "CalendarEvent", back_populates="appointment", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (
        db.CheckConstraint(
            "status IN ('held', 'confirmed', 'cancelled', 'completed', 'expired', 'leave_cancelled')",
            name="ck_appointment_status",
        ),
        # Design Document §4.1 / §6: THE double-booking guard.
        # Partial (filtered) unique index — only 'held' and
        # 'confirmed' rows block a slot; cancelled/expired/completed
        # rows don't, so a freed slot can be rebooked.
        db.Index(
            "idx_appt_no_double_book",
            "doctor_id",
            "appt_date",
            "slot_start",
            unique=True,
            postgresql_where=db.text("status IN ('held', 'confirmed')"),
        ),
        # Design Document §4.1: idx_appt_patient
        db.Index("idx_appt_patient", "patient_id", "appt_date"),
    )

    def __repr__(self):
        return f"<Appointment {self.id} doctor={self.doctor_id} {self.appt_date} {self.slot_start} {self.status}>"
