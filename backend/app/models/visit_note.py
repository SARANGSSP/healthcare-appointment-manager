from app.extensions import db


class VisitNote(db.Model):
    __tablename__ = "visit_note"

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(
        db.Integer, db.ForeignKey("appointment.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    clinical_notes = db.Column(db.Text, nullable=False)
    patient_friendly_summary = db.Column(db.Text)  # set once llm_status='ok' (§10.2)
    llm_status = db.Column(db.String(10), nullable=False, default="pending")

    appointment = db.relationship("Appointment", back_populates="visit_note")
    prescription_items = db.relationship(
        "PrescriptionItem", back_populates="visit_note", cascade="all, delete-orphan"
    )

    __table_args__ = (
        db.CheckConstraint(
            "llm_status IN ('pending', 'ok', 'failed')", name="ck_visit_note_llm_status"
        ),
    )

    def __repr__(self):
        return f"<VisitNote appt={self.appointment_id} status={self.llm_status}>"
