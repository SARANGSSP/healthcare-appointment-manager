import os
import sys

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

app = create_app(TestConfig)

def test_chunk6():
    with app.app_context():
        db.create_all()
        client = app.test_client()

        # 1. Register Admin
        res = client.post("/api/v1/auth/register", json={
            "email": "chunk6_admin@example.com",
            "password": "AdminPassword123!",
            "role": "admin",
            "full_name": "Admin User"
        })
        assert res.status_code == 201
        admin_token = res.json["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 2. Register Doctor
        doc_email = "dr_leave_test@example.com"
        res = client.post("/api/v1/auth/register", json={
            "email": doc_email,
            "password": "DoctorPassword123!",
            "role": "doctor",
            "full_name": "Dr. Mark Leave"
        })
        assert res.status_code == 201
        doc_token = res.json["access_token"]
        doc_headers = {"Authorization": f"Bearer {doc_token}"}

        # Get Doctor Profile ID
        res = client.get("/api/v1/doctors/me", headers=doc_headers)
        assert res.status_code == 200
        doc_id = res.json["doctor"]["id"]
        print(f"[OK] Doctor registered & profile ID {doc_id} retrieved")

        # 3. Register a Patient
        res = client.post("/api/v1/auth/register", json={
            "email": "patient_leave_test@example.com",
            "password": "PatientPassword123!",
            "role": "patient",
            "full_name": "Patient User"
        })
        assert res.status_code == 201
        patient_token = res.json["access_token"]
        patient_headers = {"Authorization": f"Bearer {patient_token}"}

        # 4. Patient attempts to mark leave for doctor -> expect 403
        res = client.post(f"/api/v1/doctors/{doc_id}/leave", headers=patient_headers, json={
            "leave_date": "2026-09-15"
        })
        assert res.status_code == 403, f"Expected 403, got {res.status_code}"
        print("[OK] Patient blocked from marking doctor leave (403 confirmed)")

        # 5. Doctor marks leave date
        res = client.post(f"/api/v1/doctors/{doc_id}/leave", headers=doc_headers, json={
            "leave_date": "2026-09-15",
            "reason": "Medical Conference"
        })
        assert res.status_code == 201, f"Leave mark failed: {res.json}"
        leave_data = res.json
        leave_id = leave_data["id"]
        assert leave_data["leave_date"] == "2026-09-15"
        assert leave_data["reason"] == "Medical Conference"
        print(f"[OK] Doctor marked leave for 2026-09-15 (Leave ID: {leave_id})")

        # 6. Retrieve Leave List
        res = client.get(f"/api/v1/doctors/{doc_id}/leave", headers=doc_headers)
        assert res.status_code == 200
        leaves = res.json
        assert len(leaves) == 1
        assert leaves[0]["leave_date"] == "2026-09-15"
        print("[OK] Retrieved marked leave list via GET")

        # 7. Attempt Duplicate Leave on Same Date -> expect 409
        res = client.post(f"/api/v1/doctors/{doc_id}/leave", headers=doc_headers, json={
            "leave_date": "2026-09-15"
        })
        assert res.status_code == 409, f"Expected 409, got {res.status_code}"
        print("[OK] Duplicate leave rejected with 409 Conflict")

        # 8. Delete Leave Date
        res = client.delete(f"/api/v1/doctors/{doc_id}/leave/{leave_id}", headers=doc_headers)
        assert res.status_code == 200
        print("[OK] Deleted leave date successfully")

        # 9. Verify empty list after deletion
        res = client.get(f"/api/v1/doctors/{doc_id}/leave", headers=doc_headers)
        assert res.status_code == 200
        assert len(res.json) == 0
        print("[OK] Confirmed leave list is empty after deletion")

        print("\nAll Chunk 6 Leave API tests passed cleanly!")

if __name__ == "__main__":
    test_chunk6()
