from app.extensions import db


class PrescriptionItem(db.Model):
    __tablename__ = "prescription_item"

    id = db.Column(db.Integer, primary_key=True)
    visit_note_id = db.Column(
        db.Integer, db.ForeignKey("visit_note.id", ondelete="CASCADE"), nullable=False
    )
    medication_name = db.Column(db.String(255), nullable=False)
    dosage = db.Column(db.String(100), nullable=False)
    # Free-text frequency (e.g. "twice daily", "every 8 hours") — parsed
    # into concrete reminder times by the Chunk 16 scheduling logic.
    frequency = db.Column(db.String(100), nullable=False)
    duration_days = db.Column(db.Integer, nullable=False)

    visit_note = db.relationship("VisitNote", back_populates="prescription_items")
    reminders = db.relationship(
        "MedicationReminder", back_populates="prescription_item", cascade="all, delete-orphan"
    )

    __table_args__ = (
        db.CheckConstraint("duration_days > 0", name="ck_prescription_duration_positive"),
    )

    def __repr__(self):
        return f"<PrescriptionItem {self.medication_name} ({self.frequency})>"
