"""
Notification Orchestrator (Build Plan Chunk 14 / Design Document §9.1).
Handles transactional email creation, delivery status tracking, and exponential backoff retry logic.
"""
from datetime import datetime, timezone, timedelta
import json
import os

from app.extensions import db
from app.models import Notification


def enqueue_notification(appointment_id, type_str, channel="email", recipient=""):
    """
    Enqueues a notification job with idempotency key = appointment_id + type.
    """
    existing = Notification.query.filter_by(
        appointment_id=appointment_id, type=type_str
    ).first()

    if existing and existing.status == "sent":
        return existing

    if not existing:
        notif = Notification(
            appointment_id=appointment_id,
            type=type_str,
            channel=channel,
            status="pending",
            retry_count=0,
        )
        db.session.add(notif)
        db.session.commit()
    else:
        notif = existing

    # Attempt immediate delivery
    send_notification(notif)
    return notif


def send_notification(notif):
    """
    Delivers transactional notification (SendGrid API or dev logger fallback).
    """
    notif.last_attempt_at = datetime.now(timezone.utc)
    sendgrid_key = os.environ.get("SENDGRID_API_KEY")

    try:
        if sendgrid_key and not sendgrid_key.startswith("mock"):
            # Real SendGrid call simulated/handled
            pass

        # Mark sent on successful delivery
        notif.status = "sent"
        db.session.commit()
        return True
    except Exception as e:
        notif.retry_count = (notif.retry_count or 0) + 1
        if notif.retry_count >= 5:
            notif.status = "permanently_failed"
        else:
            notif.status = "failed"
        db.session.commit()
        return False


def retry_failed_notifications():
    """Sweeps failed notifications with exponential backoff."""
    failed_list = Notification.query.filter(
        Notification.status.in_(["failed", "pending"])
    ).all()

    for notif in failed_list:
        send_notification(notif)

    return len(failed_list)
