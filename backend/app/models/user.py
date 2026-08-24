from datetime import datetime, timezone

from app.extensions import db


class User(db.Model):
    """
    Design Document §4: role is a single table with a role column
    rather than separate patient/doctor/admin tables at the auth
    level — patient_profile / doctor_profile hang off this 1:0..1
    (admin has no profile table; it's just a role with no extra
    fields per the brief).
    """

    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    # B4 fix: persist OAuth tokens on the User
    google_access_token = db.Column(db.String(512), nullable=True)
    google_refresh_token = db.Column(db.String(512), nullable=True)

    patient_profile = db.relationship(
        "PatientProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    doctor_profile = db.relationship(
        "DoctorProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (
        db.CheckConstraint("role IN ('patient', 'doctor', 'admin')", name="ck_user_role"),
    )

    def __repr__(self):
        return f"<User {self.id} {self.email} ({self.role})>"
