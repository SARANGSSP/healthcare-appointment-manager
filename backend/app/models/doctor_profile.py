from app.extensions import db


class DoctorProfile(db.Model):
    __tablename__ = "doctor_profile"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    full_name = db.Column(db.String(255), nullable=False)
    specialisation = db.Column(db.String(100), nullable=False, index=True)
    # e.g. {"mon": ["09:00-13:00", "14:00-17:00"], "tue": [...], ...}
    working_hours = db.Column(db.JSON, nullable=False, default=dict)
    slot_duration_minutes = db.Column(db.Integer, nullable=False, default=20)

    user = db.relationship("User", back_populates="doctor_profile")
    leave_days = db.relationship(
        "DoctorLeave", back_populates="doctor", cascade="all, delete-orphan"
    )
    appointments = db.relationship("Appointment", back_populates="doctor")

    __table_args__ = (
        db.CheckConstraint("slot_duration_minutes > 0", name="ck_doctor_slot_duration_positive"),
    )

    def __repr__(self):
        return f"<DoctorProfile {self.id} {self.full_name} ({self.specialisation})>"
