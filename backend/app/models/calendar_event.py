from app.extensions import db


class CalendarEvent(db.Model):
    __tablename__ = "calendar_event"

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(
        db.Integer, db.ForeignKey("appointment.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    patient_google_event_id = db.Column(db.String(255))
    doctor_google_event_id = db.Column(db.String(255))
    sync_status = db.Column(db.String(20), nullable=False, default="pending")

    appointment = db.relationship("Appointment", back_populates="calendar_event")

    __table_args__ = (
        db.CheckConstraint(
            "sync_status IN ('pending', 'synced', 'failed', 'permanently_failed')",
            name="ck_calendar_event_sync_status",
        ),
    )

    def __repr__(self):
        return f"<CalendarEvent appt={self.appointment_id} {self.sync_status}>"
