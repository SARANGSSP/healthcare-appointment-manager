from datetime import datetime, timezone
from app.extensions import db


class Notification(db.Model):
    __tablename__ = "notification"

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(
        db.Integer, db.ForeignKey("appointment.id", ondelete="CASCADE"), nullable=False
    )
    # Re-aligned length to 20 to match spec/migration type check
    type = db.Column(db.String(20), nullable=False)
    channel = db.Column(db.String(20), nullable=False, default="email")
    # H2 fix: recipient email stored so SendGrid knows where to send
    recipient = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="pending")
    retry_count = db.Column(db.Integer, nullable=False, default=0)
    last_attempt_at = db.Column(db.DateTime(timezone=True))
    # B1 fix: add created_at column
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    appointment = db.relationship("Appointment", back_populates="notifications")

    __table_args__ = (
        # B2 & B11 fix: Re-aligned types back to original spec constraints
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
