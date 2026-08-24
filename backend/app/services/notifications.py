"""
Notification Orchestrator (Build Plan Chunk 14 / Design Document §9.1).
Handles transactional email creation, delivery status tracking, and exponential backoff retry logic.

H2 fix: send_notification() now makes a real HTTP POST to the SendGrid v3 API
        when SENDGRID_API_KEY is set. Previously the real call was `pass`.
H3 fix: retry logic with backoff is now handled by the Celery beat task
        (tasks.retry_notifications_task) which respects the 1m/5m/30m windows.
        retry_failed_notifications() is kept for direct calling / testing.
"""
from datetime import datetime, timezone, timedelta
import json
import os
import urllib.request
import urllib.error

from flask import current_app

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
            recipient=recipient,
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
    Delivers transactional notification via SendGrid API (H2 fix).
    Falls back to dev logger when SENDGRID_API_KEY is absent or prefixed with 'mock'.
    """
    notif.last_attempt_at = datetime.now(timezone.utc)

    # M1-style: prefer current_app.config, fall back to os.environ
    try:
        sendgrid_key = current_app.config.get("SENDGRID_API_KEY") or os.environ.get("SENDGRID_API_KEY", "")
    except RuntimeError:
        sendgrid_key = os.environ.get("SENDGRID_API_KEY", "")

    try:
        if sendgrid_key and not sendgrid_key.startswith("mock"):
            # H2 fix: real SendGrid v3 API call
            _sendgrid_send(notif, sendgrid_key)
        else:
            # Dev/test: log to stdout, treat as sent
            print(f"[NOTIFICATION DEV] {notif.type} for appointment {notif.appointment_id}")

        notif.status = "sent"
        db.session.commit()
        return True

    except Exception as e:
        notif.retry_count = (notif.retry_count or 0) + 1
        notif.status = "permanently_failed" if notif.retry_count >= 5 else "failed"
        db.session.commit()
        return False


def _sendgrid_send(notif, api_key: str):
    """
    Makes the real HTTP POST to SendGrid /v3/mail/send.
    Raises on non-2xx to let send_notification handle retry bookkeeping.
    """
    # Determine recipient — stored on notif if column exists, else use placeholder
    to_email = getattr(notif, "recipient", None) or "patient@example.com"

    subject_map = {
        "confirmation": "Your appointment is confirmed",
        "cancellation": "Your appointment has been cancelled",
        "leave_notice": "Your appointment was cancelled (doctor leave)",
        "reminder": "Medication reminder",
    }
    subject = subject_map.get(notif.type, "Healthcare Appointment Manager")
    body_text = (
        f"Notification type: {notif.type}\n"
        f"Appointment ID: {notif.appointment_id}\n"
        "Please log in to view full details."
    )

    payload = json.dumps({
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": "noreply@healthcare-manager.app"},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body_text}],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=10) as resp:
        status = resp.getcode()
        if status not in (200, 202):
            raise RuntimeError(f"SendGrid responded with HTTP {status}")


def retry_failed_notifications(force=False):
    """
    Sweeps failed/pending notifications and retries them, respecting backoff timing unless force=True.
    Called directly from tests and from tasks.retry_notifications_task (B12).
    """
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    # Backoff windows per retry_count: 0→1 min, 1→5 min, 2→30 min, 3+→60 min
    BACKOFF_MINUTES = {0: 1, 1: 5, 2: 30}

    failed_list = Notification.query.filter(
        Notification.status.in_(["failed", "pending"]),
        Notification.retry_count < 5,
    ).all()

    retried = 0
    for notif in failed_list:
        if not force and notif.last_attempt_at:
            wait_minutes = BACKOFF_MINUTES.get(notif.retry_count or 0, 60)
            last = notif.last_attempt_at
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            if (now - last).total_seconds() < wait_minutes * 60:
                continue
        send_notification(notif)
        retried += 1

    return retried
