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

def test_chunk5():
    with app.app_context():
        db.create_all()

        client = app.test_client()

        # 1. Register Admin User
        admin_email = "chunk5_admin@example.com"
        admin_pass = "AdminPass123!"
        res = client.post("/api/v1/auth/register", json={
            "email": admin_email,
            "password": admin_pass,
            "role": "admin",
            "full_name": "System Admin"
        })
        assert res.status_code == 201, f"Admin register failed: {res.json}"
        admin_token = res.json["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        print("[OK] Admin registered & token acquired")

        # 2. Register Patient User
        patient_email = "chunk5_patient@example.com"
        res = client.post("/api/v1/auth/register", json={
            "email": patient_email,
            "password": "PatientPass123!",
            "role": "patient",
            "full_name": "Jane Patient"
        })
        assert res.status_code == 201
        patient_token = res.json["access_token"]
        patient_headers = {"Authorization": f"Bearer {patient_token}"}
        print("[OK] Patient registered & token acquired")

        # 3. Patient tries to create doctor -> expect 403
        res = client.post("/api/v1/doctors", headers=patient_headers, json={
            "email": "unauthorized_doc@example.com",
            "password": "DocPassword123!",
            "full_name": "Dr. Unauthorized",
            "specialisation": "Cardiology"
        })
        assert res.status_code == 403, f"Expected 403, got {res.status_code}"
        print("[OK] Patient blocked from creating doctor (403 confirmed)")

        # 4. Admin creates Doctor
        doc_email = "dr_smith@example.com"
        res = client.post("/api/v1/doctors", headers=admin_headers, json={
            "email": doc_email,
            "password": "DocPassword123!",
            "full_name": "Dr. Alice Smith",
            "specialisation": "Neurology",
            "slot_duration_minutes": 15
        })
        assert res.status_code == 201, f"Admin create doctor failed: {res.json}"
        doc_data = res.json
        doc_id = doc_data["id"]
        assert doc_data["full_name"] == "Dr. Alice Smith"
        assert doc_data["specialisation"] == "Neurology"
        assert doc_data["slot_duration_minutes"] == 15
        print(f"[OK] Admin created Doctor ID {doc_id} successfully")

        # 5. List Doctors
        res = client.get("/api/v1/doctors", headers=admin_headers)
        assert res.status_code == 200
        docs_list = res.json
        assert len(docs_list) >= 1
        assert any(d["id"] == doc_id for d in docs_list)
        print("[OK] Doctor listed in GET /api/v1/doctors")

        # 6. Get Single Doctor
        res = client.get(f"/api/v1/doctors/{doc_id}", headers=admin_headers)
        assert res.status_code == 200
        assert res.json["id"] == doc_id
        print("[OK] Retrieved doctor profile details by ID")

        # 7. Update Doctor Profile
        res = client.put(f"/api/v1/doctors/{doc_id}", headers=admin_headers, json={
            "full_name": "Dr. Alice Smith MD",
            "specialisation": "Pediatric Neurology",
            "slot_duration_minutes": 30
        })
        assert res.status_code == 200
        updated = res.json
        assert updated["full_name"] == "Dr. Alice Smith MD"
        assert updated["specialisation"] == "Pediatric Neurology"
        assert updated["slot_duration_minutes"] == 30
        print("[OK] Doctor profile updated via PUT")

        # 8. Delete Doctor
        res = client.delete(f"/api/v1/doctors/{doc_id}", headers=admin_headers)
        assert res.status_code == 200
        print("[OK] Doctor deleted via DELETE")

        # 9. Confirm 404 after deletion
        res = client.get(f"/api/v1/doctors/{doc_id}", headers=admin_headers)
        assert res.status_code == 404
        print("[OK] Confirmed 404 after deletion")

        print("\nAll Chunk 5 API tests passed cleanly!")

if __name__ == "__main__":
    test_chunk5()
