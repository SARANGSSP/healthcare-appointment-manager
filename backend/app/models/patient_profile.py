from app.extensions import db


class PatientProfile(db.Model):
    __tablename__ = "patient_profile"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    full_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(30))
    dob = db.Column(db.Date)

    user = db.relationship("User", back_populates="patient_profile")
    appointments = db.relationship("Appointment", back_populates="patient")

    def __repr__(self):
        return f"<PatientProfile {self.id} {self.full_name}>"
