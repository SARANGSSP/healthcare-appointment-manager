from app.extensions import db


class DoctorLeave(db.Model):
    __tablename__ = "doctor_leave"

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(
        db.Integer, db.ForeignKey("doctor_profile.id", ondelete="CASCADE"), nullable=False
    )
    leave_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(255))

    doctor = db.relationship("DoctorProfile", back_populates="leave_days")

    __table_args__ = (
        # Design Document §4.1: idx_leave_doctor_date
        db.Index("idx_leave_doctor_date", "doctor_id", "leave_date"),
        # M4 fix: enforce uniqueness at DB level to eliminate TOCTOU race
        db.UniqueConstraint("doctor_id", "leave_date", name="uq_doctor_leave_date"),
    )

    def __repr__(self):
        return f"<DoctorLeave doctor={self.doctor_id} {self.leave_date}>"
