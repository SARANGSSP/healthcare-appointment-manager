"""
Minimal doctor-only route, added in Chunk 3 purely to demonstrate
the role middleware end-to-end (Build Plan Chunk 3 'done when': "a
patient token is rejected by a doctor-only route"). Chunk 5 (Doctor
& Admin Profile Management) replaces this stub with real profile
CRUD under the same /doctors prefix.
"""
from flask import Blueprint, g, jsonify

from app.auth.decorators import login_required, role_required

doctors_bp = Blueprint("doctors", __name__)


@doctors_bp.get("/doctors/me")
@login_required
@role_required("doctor")
def doctor_me():
    return jsonify({"role": g.current_user["role"], "message": "Doctor-only route reached"})
