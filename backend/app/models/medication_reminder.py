from app.extensions import db


class MedicationReminder(db.Model):
    __tablename__ = "medication_reminder"

    id = db.Column(db.Integer, primary_key=True)
    prescription_item_id = db.Column(
        db.Integer, db.ForeignKey("prescription_item.id", ondelete="CASCADE"), nullable=False
    )
    scheduled_for = db.Column(db.DateTime(timezone=True), nullable=False)
    status = db.Column(db.String(10), nullable=False, default="pending")

    prescription_item = db.relationship("PrescriptionItem", back_populates="reminders")

    __table_args__ = (
        db.CheckConstraint(
            "status IN ('pending', 'sent', 'failed')", name="ck_medication_reminder_status"
        ),
        # Design Document §4.1: idx_reminder_due — the worker's poll
        # query is "due reminders not yet sent", so status leads.
        db.Index("idx_reminder_due", "status", "scheduled_for"),
    )

    def __repr__(self):
        return f"<MedicationReminder {self.id} {self.scheduled_for} {self.status}>"
