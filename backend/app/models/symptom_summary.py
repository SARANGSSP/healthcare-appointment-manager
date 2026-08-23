from app.extensions import db


class SymptomSummary(db.Model):
    __tablename__ = "symptom_summary"

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(
        db.Integer, db.ForeignKey("appointment.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    raw_symptoms = db.Column(db.Text, nullable=False)
    urgency = db.Column(db.String(10))  # Low / Medium / High, set once llm_status='ok'
    chief_complaint = db.Column(db.Text)
    suggested_questions = db.Column(db.JSON)  # list[str], up to 3 (§10.1)
    llm_status = db.Column(db.String(10), nullable=False, default="pending")

    appointment = db.relationship("Appointment", back_populates="symptom_summary")

    __table_args__ = (
        db.CheckConstraint(
            "urgency IS NULL OR urgency IN ('Low', 'Medium', 'High')",
            name="ck_symptom_summary_urgency",
        ),
        db.CheckConstraint(
            "llm_status IN ('pending', 'ok', 'failed')", name="ck_symptom_summary_llm_status"
        ),
    )

    def __repr__(self):
        return f"<SymptomSummary appt={self.appointment_id} status={self.llm_status}>"
