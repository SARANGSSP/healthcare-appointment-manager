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


@health_bp.post("/seed-demo")
def seed_demo():
    """
    Populates the DB with realistic demo data for presentations.
    Protected by SEED_SECRET. Safe to run multiple times (skips if demo data exists).
    POST /api/v1/seed-demo  Body: { "secret": "<SEED_SECRET>" }
    """
    import os, bcrypt
    from datetime import date, time, timedelta
    from app.models.user import User
    from app.models.doctor_profile import DoctorProfile
    from app.models.patient_profile import PatientProfile
    from app.models.appointment import Appointment

    seed_secret = os.environ.get("SEED_SECRET", "")
    if not seed_secret:
        return jsonify({"error": "SEED_SECRET not configured"}), 403
    data = request.get_json(silent=True) or {}
    if data.get("secret") != seed_secret:
        return jsonify({"error": "Invalid secret"}), 403

    if DoctorProfile.query.count() > 0:
        if not data.get("force"):
            return jsonify({"message": "Demo data already exists. Pass force:true to wipe and re-seed."}), 200
        # Wipe existing demo data
        from app.models.doctor_profile import DoctorProfile as DP
        from app.models.patient_profile import PatientProfile as PP
        from app.models.user import User as U
        demo_emails = [d.user.email for d in DP.query.all()] + [p.user.email for p in PP.query.all()]
        for u in U.query.filter(U.email.in_(demo_emails)).all():
            db.session.delete(u)
        db.session.commit()


    demo_password = bcrypt.hashpw(b"Demo@1234", bcrypt.gensalt()).decode("utf-8")

    # --- Doctors ---
    doctors_data = [
        ("dr.sarah.johnson@healthdemo.com", "Dr. Sarah Johnson", "Cardiology",
         {"mon": ["09:00-13:00", "14:00-17:00"], "tue": ["09:00-13:00", "14:00-17:00"],
          "wed": ["09:00-13:00"], "thu": ["09:00-13:00", "14:00-17:00"], "fri": ["09:00-12:00"]}),
        ("dr.michael.chen@healthdemo.com", "Dr. Michael Chen", "Orthopedics",
         {"mon": ["10:00-14:00"], "tue": ["10:00-14:00", "15:00-18:00"],
          "wed": ["10:00-14:00", "15:00-18:00"], "thu": ["10:00-14:00"], "fri": ["10:00-13:00"]}),
        ("dr.emily.rodriguez@healthdemo.com", "Dr. Emily Rodriguez", "General Practice",
         {"mon": ["08:00-12:00", "13:00-17:00"], "tue": ["08:00-12:00", "13:00-17:00"],
          "wed": ["08:00-12:00"], "thu": ["08:00-12:00", "13:00-17:00"], "fri": ["08:00-12:00"]}),
    ]
    doctors = []
    for email, name, spec, hours in doctors_data:
        u = User(email=email, password_hash=demo_password, role="doctor")
        db.session.add(u)
        db.session.flush()
        dp = DoctorProfile(user_id=u.id, full_name=name, specialisation=spec,
                           working_hours=hours, slot_duration_minutes=20)
        db.session.add(dp)
        db.session.flush()
        doctors.append(dp)

    # --- Patients ---
    patients_data = [
        ("john.smith@demo.com",    "John Smith",    "+1-555-0101", date(1985, 3, 15)),
        ("mary.williams@demo.com", "Mary Williams", "+1-555-0102", date(1990, 7, 22)),
        ("robert.brown@demo.com",  "Robert Brown",  "+1-555-0103", date(1978, 11, 8)),
        ("jennifer.davis@demo.com","Jennifer Davis", "+1-555-0104", date(1995, 1, 30)),
    ]
    patients = []
    for email, name, phone, dob in patients_data:
        u = User(email=email, password_hash=demo_password, role="patient")
        db.session.add(u)
        db.session.flush()
        pp = PatientProfile(user_id=u.id, full_name=name, phone=phone, dob=dob)
        db.session.add(pp)
        db.session.flush()
        patients.append(pp)

    # --- Appointments ---
    from datetime import datetime, timezone
    today = date.today()

    appts = [
        # Completed past appointments
        (patients[0], doctors[0], today - timedelta(days=14), time(9,0),  time(9,20),  "completed"),
        (patients[1], doctors[2], today - timedelta(days=10), time(8,0),  time(8,20),  "completed"),
        (patients[2], doctors[1], today - timedelta(days=7),  time(10,0), time(10,20), "completed"),
        (patients[3], doctors[0], today - timedelta(days=5),  time(14,0), time(14,20), "completed"),
        (patients[0], doctors[2], today - timedelta(days=3),  time(9,0),  time(9,20),  "completed"),
        # Cancelled
        (patients[1], doctors[1], today - timedelta(days=6),  time(10,0), time(10,20), "cancelled"),
        (patients[3], doctors[2], today - timedelta(days=2),  time(13,0), time(13,20), "cancelled"),
        # Upcoming confirmed
        (patients[0], doctors[0], today + timedelta(days=2),  time(9,0),  time(9,20),  "confirmed"),
        (patients[1], doctors[2], today + timedelta(days=3),  time(8,0),  time(8,20),  "confirmed"),
        (patients[2], doctors[0], today + timedelta(days=5),  time(14,0), time(14,20), "confirmed"),
        (patients[3], doctors[1], today + timedelta(days=7),  time(10,0), time(10,20), "confirmed"),
        (patients[0], doctors[2], today + timedelta(days=10), time(9,0),  time(9,20),  "confirmed"),
    ]
    now = datetime.now(timezone.utc)
    for pat, doc, appt_date, start, end, status in appts:
        appt = Appointment(
            patient_id=pat.id, doctor_id=doc.id,
            appt_date=appt_date, slot_start=start, slot_end=end,
            status=status, held_at=now,
            confirmed_at=now if status in ("confirmed", "completed") else None,
        )
        db.session.add(appt)

    db.session.commit()
    return jsonify({
        "message": "Demo data seeded successfully!",
        "doctors": len(doctors),
        "patients": len(patients),
        "appointments": len(appts),
        "login_password": "Demo@1234",
        "sample_logins": {
            "doctor": "dr.sarah.johnson@healthdemo.com",
            "patient": "john.smith@demo.com",
        }
    }), 201


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
