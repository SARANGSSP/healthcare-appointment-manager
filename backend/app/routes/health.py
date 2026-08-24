from flask import Blueprint, current_app, jsonify, request

from app.auth.decorators import login_required, role_required
from app.models import Appointment, DoctorProfile, Notification, PatientProfile
from app.services.notifications import send_notification
from app.extensions import db

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "service": "healthcare-appointment-manager-api",
            "env": current_app.config.get("ENV", "unknown"),
        }
    )


@health_bp.post("/seed-admin")
def seed_admin():
    """
    One-time admin seed endpoint. Protected by SEED_SECRET env var.
    POST /api/v1/seed-admin
    Body: { "secret": "<SEED_SECRET>", "email": "...", "password": "..." }
    """
    import os
    import bcrypt
    from app.models.user import User

    seed_secret = os.environ.get("SEED_SECRET", "")
    if not seed_secret:
        return jsonify({"error": "SEED_SECRET not configured on server"}), 403

    data = request.get_json(silent=True) or {}
    if data.get("secret") != seed_secret:
        return jsonify({"error": "Invalid secret"}), 403

    email = data.get("email", "admin@example.com")
    password = data.get("password", "changeme123")

    existing = User.query.filter_by(email=email).first()
    if existing:
        return jsonify({"message": f"User {email} already exists", "role": existing.role}), 200

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    u = User(email=email, password_hash=password_hash, role="admin")
    db.session.add(u)
    db.session.commit()
    return jsonify({"message": f"Admin created: {email}"}), 201


@health_bp.post("/reset-password")
def reset_password():
    """
    Emergency password reset. Protected by SEED_SECRET.
    POST /api/v1/reset-password
    Body: { "secret": "<SEED_SECRET>", "email": "...", "new_password": "..." }
    """
    import os
    import bcrypt
    from app.models.user import User

    seed_secret = os.environ.get("SEED_SECRET", "")
    if not seed_secret:
        return jsonify({"error": "SEED_SECRET not configured"}), 403

    data = request.get_json(silent=True) or {}
    if data.get("secret") != seed_secret:
        return jsonify({"error": "Invalid secret"}), 403

    email = data.get("email")
    new_password = data.get("new_password")
    if not email or not new_password:
        return jsonify({"error": "email and new_password required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": f"User {email} not found"}), 404

    user.password_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    db.session.commit()
    return jsonify({"message": f"Password reset for {email}"}), 200


@health_bp.get("/admin/overview")
@login_required
@role_required("admin")
def admin_overview():
    """GET /api/v1/admin/overview (Chunk 18)"""
    total_bookings = Appointment.query.count()
    active_doctors = DoctorProfile.query.count()
    total_patients = PatientProfile.query.count()
    failed_notifications = Notification.query.filter(
        Notification.status.in_(["failed", "permanently_failed"])
    ).count()

    return jsonify({
        "total_bookings": total_bookings,
        "active_doctors": active_doctors,
        "total_patients": total_patients,
        "failed_notifications": failed_notifications,
        "system_status": "healthy",
    }), 200


@health_bp.get("/admin/notifications")
@login_required
@role_required("admin")
def admin_notifications():
    """GET /api/v1/admin/notifications (Chunk 14)"""
    notifs = Notification.query.order_by(Notification.created_at.desc()).all()
    result = []
    for n in notifs:
        result.append({
            "id": n.id,
            "appointment_id": n.appointment_id,
            "type": n.type,
            "channel": n.channel,
            "status": n.status,
            "retry_count": n.retry_count,
            "last_attempt_at": n.last_attempt_at.isoformat() if n.last_attempt_at else None,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        })
    return jsonify(result), 200


@health_bp.post("/admin/notifications/<int:notification_id>/retry")
@login_required
@role_required("admin")
def admin_retry_notification(notification_id):
    """POST /api/v1/admin/notifications/{id}/retry (Chunk 14)"""
    notif = Notification.query.get(notification_id)
    if not notif:
        return jsonify({"error": {"code": "not_found", "message": "Notification not found"}}), 404

    success = send_notification(notif)
    return jsonify({
        "message": "Notification retried successfully" if success else "Retry attempt failed",
        "status": notif.status,
        "retry_count": notif.retry_count,
    }), 200
