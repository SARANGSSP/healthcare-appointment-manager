import os
import sys
from datetime import datetime, time

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
from app.models import Appointment, DoctorLeave, DoctorProfile, PatientProfile, User

app = create_app(TestConfig)

def test_chunk7():
    with app.app_context():
        db.create_all()
        client = app.test_client()

        # 1. Register Admin
        res = client.post("/api/v1/auth/register", json={
            "email": "chunk7_admin@example.com",
            "password": "AdminPassword123!",
            "role": "admin",
            "full_name": "Admin User"
        })
        assert res.status_code == 201
        admin_token = res.json["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 2. Create Doctor A (Cardiology) & Doctor B (Neurology)
        res = client.post("/api/v1/doctors", headers=admin_headers, json={
            "email": "dr_heart@example.com",
            "password": "DocPassword123!",
            "full_name": "Dr. Heart",
            "specialisation": "Cardiology",
            "slot_duration_minutes": 20
        })
        assert res.status_code == 201
        doc_a_id = res.json["id"]

        res = client.post("/api/v1/doctors", headers=admin_headers, json={
            "email": "dr_brain@example.com",
            "password": "DocPassword123!",
            "full_name": "Dr. Brain",
            "specialisation": "Neurology",
            "slot_duration_minutes": 30
        })
        assert res.status_code == 201
        doc_b_id = res.json["id"]
        print(f"[OK] Created Doctor A (ID {doc_a_id}) and Doctor B (ID {doc_b_id})")

        # 3. Register Patient
        res = client.post("/api/v1/auth/register", json={
            "email": "chunk7_patient@example.com",
            "password": "PatientPassword123!",
            "role": "patient",
            "full_name": "Jane Patient"
        })
        assert res.status_code == 201
        patient_token = res.json["access_token"]
        patient_headers = {"Authorization": f"Bearer {patient_token}"}
        patient_profile_id = PatientProfile.query.filter_by(full_name="Jane Patient").first().id

        # 4. Patient filters doctors by specialisation "Cardiology"
        res = client.get("/api/v1/doctors?specialisation=Cardiology", headers=patient_headers)
        assert res.status_code == 200
        filtered_docs = res.json
        assert len(filtered_docs) == 1
        assert filtered_docs[0]["id"] == doc_a_id
        print("[OK] Specialisation filtering working as expected")

        # 5. Check Availability for Doctor A on a Wednesday (2026-08-26)
        target_date = "2026-08-26"
        res = client.get(f"/api/v1/doctors/{doc_a_id}/availability?date={target_date}", headers=patient_headers)
        assert res.status_code == 200
        avail = res.json
        assert avail["on_leave"] is False
        assert avail["slot_duration_minutes"] == 20
        assert len(avail["slots"]) > 0
        assert all(s["status"] == "available" for s in avail["slots"])
        print(f"[OK] Computed {len(avail['slots'])} free 20-min slots for Doctor A on {target_date}")

        # 6. Insert a confirmed appointment at 09:20
        appt_date_obj = datetime.strptime(target_date, "%Y-%m-%d").date()
        appt = Appointment(
            patient_id=patient_profile_id,
            doctor_id=doc_a_id,
            appt_date=appt_date_obj,
            slot_start=time(9, 20),
            slot_end=time(9, 40),
            status="confirmed"
        )
        db.session.add(appt)
        db.session.commit()

        # 7. Re-query availability -> 09:20 must be 'taken'
        res = client.get(f"/api/v1/doctors/{doc_a_id}/availability?date={target_date}", headers=patient_headers)
        assert res.status_code == 200
        updated_avail = res.json
        slot_920 = next(s for s in updated_avail["slots"] if s["start_time"] == "09:20")
        slot_900 = next(s for s in updated_avail["slots"] if s["start_time"] == "09:00")
        assert slot_920["status"] == "taken"
        assert slot_900["status"] == "available"
        print("[OK] Confirmed appointment correctly marks slot 09:20 as 'taken'")

        # 8. Mark Doctor A on leave for 2026-08-26
        res = client.post(f"/api/v1/doctors/{doc_a_id}/leave", headers=admin_headers, json={
            "leave_date": target_date,
            "reason": "Emergency Leave"
        })
        assert res.status_code == 201

        # 9. Re-query availability -> must return on_leave: True and slots: []
        res = client.get(f"/api/v1/doctors/{doc_a_id}/availability?date={target_date}", headers=patient_headers)
        assert res.status_code == 200
        leave_avail = res.json
        assert leave_avail["on_leave"] is True
        assert leave_avail["leave_reason"] == "Emergency Leave"
        assert len(leave_avail["slots"]) == 0
        print("[OK] Leave date override correctly returns on_leave: True and empty slots")

        print("\nAll Chunk 7 Availability Search API tests passed cleanly!")

if __name__ == "__main__":
    test_chunk7()
