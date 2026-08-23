import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SECRET_KEY = "test-secret"
    JWT_SECRET = "test-jwt-secret"
    JWT_ACCESS_TOKEN_EXPIRES_MINUTES = 60
    JWT_REFRESH_TOKEN_EXPIRES_DAYS = 7

from app import create_app
from app.extensions import db
from app.models import Appointment, DoctorProfile, PatientProfile, SymptomSummary, User
from app.routes.appointments import _sweep_expired_holds

app = create_app(TestConfig)

def test_chunks8_9():
    with app.app_context():
        db.create_all()
        client = app.test_client()

        # 1. Register Admin
        res = client.post("/api/v1/auth/register", json={
            "email": "booking_admin@example.com",
            "password": "AdminPassword123!",
            "role": "admin",
            "full_name": "Admin User"
        })
        assert res.status_code == 201
        admin_token = res.json["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 2. Create Doctor
        res = client.post("/api/v1/doctors", headers=admin_headers, json={
            "email": "dr_booking@example.com",
            "password": "DocPassword123!",
            "full_name": "Dr. Booking Test",
            "specialisation": "Cardiology",
            "slot_duration_minutes": 20
        })
        assert res.status_code == 201
        doc_id = res.json["id"]
        print(f"[OK] Doctor profile created with ID {doc_id}")

        # 3. Register Patient A & Patient B
        res = client.post("/api/v1/auth/register", json={
            "email": "patient_a@example.com",
            "password": "PatientPassword123!",
            "role": "patient",
            "full_name": "Patient A"
        })
        assert res.status_code == 201
        patient_a_token = res.json["access_token"]
        patient_a_headers = {"Authorization": f"Bearer {patient_a_token}"}

        res = client.post("/api/v1/auth/register", json={
            "email": "patient_b@example.com",
            "password": "PatientPassword123!",
            "role": "patient",
            "full_name": "Patient B"
        })
        assert res.status_code == 201
        patient_b_token = res.json["access_token"]
        patient_b_headers = {"Authorization": f"Bearer {patient_b_token}"}
        print("[OK] Patient A and Patient B accounts registered")

        # 4. Patient A holds slot 09:00-09:20 for date 2026-08-28
        target_date = "2026-08-28"
        res = client.post("/api/v1/appointments/hold", headers=patient_a_headers, json={
            "doctor_id": doc_id,
            "appt_date": target_date,
            "slot_start": "09:00",
            "slot_end": "09:20"
        })
        assert res.status_code == 201, f"Hold failed: {res.json}"
        hold_a = res.json
        appt_a_id = hold_a["id"]
        assert hold_a["status"] == "held"
        assert hold_a["ttl_seconds"] <= 300
        print(f"[OK] Patient A held slot 09:00-09:20 (Appt ID: {appt_a_id}, TTL: {hold_a['ttl_seconds']}s)")

        # 5. Patient B attempts to hold the SAME slot -> expect 409 Conflict
        res = client.post("/api/v1/appointments/hold", headers=patient_b_headers, json={
            "doctor_id": doc_id,
            "appt_date": target_date,
            "slot_start": "09:00",
            "slot_end": "09:20"
        })
        assert res.status_code == 409, f"Expected 409 Conflict, got {res.status_code}"
        print("[OK] Double-booking hold attempt by Patient B correctly rejected with 409 Conflict")

        # 6. Patient A confirms booking with symptoms
        symptoms_text = "Fever, shortness of breath, fatigue for 3 days"
        res = client.post(f"/api/v1/appointments/{appt_a_id}/confirm", headers=patient_a_headers, json={
            "symptoms": symptoms_text
        })
        assert res.status_code == 200, f"Confirm failed: {res.json}"
        confirmed_a = res.json
        assert confirmed_a["status"] == "confirmed"
        assert confirmed_a["confirmed_at"] is not None
        assert confirmed_a["symptoms"] == symptoms_text
        print("[OK] Patient A confirmed booking with symptoms saved in SymptomSummary")

        # 7. Patient B attempts to hold the confirmed slot -> expect 409 Conflict
        res = client.post("/api/v1/appointments/hold", headers=patient_b_headers, json={
            "doctor_id": doc_id,
            "appt_date": target_date,
            "slot_start": "09:00",
            "slot_end": "09:20"
        })
        assert res.status_code == 409
        print("[OK] Confirmed slot blocked Patient B with 409 Conflict")

        # 8. Test Hold Expiration & Sweeper: Patient A holds slot 09:20-09:40
        res = client.post("/api/v1/appointments/hold", headers=patient_a_headers, json={
            "doctor_id": doc_id,
            "appt_date": target_date,
            "slot_start": "09:20",
            "slot_end": "09:40"
        })
        assert res.status_code == 201
        appt_expire_id = res.json["id"]

        # Simulate hold older than 300 seconds
        appt_obj = db.session.get(Appointment, appt_expire_id)
        appt_obj.held_at = datetime.now(timezone.utc) - timedelta(seconds=360)
        db.session.commit()

        # Run sweeper
        _sweep_expired_holds()

        # Verify status is now 'expired'
        rechecked_appt = db.session.get(Appointment, appt_expire_id)
        assert rechecked_appt.status == "expired"
        print("[OK] Sweeper correctly expired stale hold older than 300s")

        # 9. Patient B can now hold slot 09:20-09:40 after expiration
        res = client.post("/api/v1/appointments/hold", headers=patient_b_headers, json={

            "doctor_id": doc_id,
            "appt_date": target_date,
            "slot_start": "09:20",
            "slot_end": "09:40"
        })
        assert res.status_code == 201, f"Re-hold failed: {res.json}"

        print("[OK] Expired slot 09:20-09:40 was successfully re-held by Patient B")

        print("\nAll Chunks 8 & 9 Slot Hold & Booking Guarantee tests passed cleanly!")

if __name__ == "__main__":
    test_chunks8_9()
