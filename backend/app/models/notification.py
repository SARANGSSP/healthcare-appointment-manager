from app.extensions import db


class Notification(db.Model):
    __tablename__ = "notification"

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(
        db.Integer, db.ForeignKey("appointment.id", ondelete="CASCADE"), nullable=False
    )
    type = db.Column(db.String(20), nullable=False)
    channel = db.Column(db.String(20), nullable=False, default="email")
    status = db.Column(db.String(20), nullable=False, default="pending")
    retry_count = db.Column(db.Integer, nullable=False, default=0)
    last_attempt_at = db.Column(db.DateTime(timezone=True))

    appointment = db.relationship("Appointment", back_populates="notifications")

    __table_args__ = (
        db.CheckConstraint(
            "type IN ('confirmation', 'reminder', 'cancellation', 'leave_notice')",
            name="ck_notification_type",
        ),
        db.CheckConstraint("channel = 'email'", name="ck_notification_channel"),
        db.CheckConstraint(
            "status IN ('pending', 'sent', 'failed', 'permanently_failed')",
            name="ck_notification_status",
        ),
        db.CheckConstraint("retry_count >= 0", name="ck_notification_retry_count_nonneg"),
    )

    def __repr__(self):
        return f"<Notification {self.id} {self.type} {self.status}>"
