from flask import Blueprint, current_app, jsonify

from app.auth.decorators import login_required, role_required
from app.models import Appointment, DoctorProfile, Notification, PatientProfile
from app.services.notifications import send_notification

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
