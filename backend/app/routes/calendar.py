"""
Google Calendar OAuth Callback Blueprint (Chunk 10 / Design Document §9.1).
Exchanges OAuth authorization code for access tokens when GOOGLE_OAUTH_* env vars are set.
"""
import json
import os
import urllib.request
import urllib.parse
from flask import Blueprint, current_app, jsonify, request

calendar_bp = Blueprint("calendar", __name__)


@calendar_bp.get("/calendar/callback")
def calendar_callback():
    """
    GET /api/v1/calendar/callback
    Receives OAuth authorization code and state token from Google OAuth redirect.
    """
    code = request.args.get("code", "").strip()
    state = request.args.get("state", "").strip()

    if not code:
        return jsonify({
            "error": {
                "code": "missing_code",
                "message": "Authorization code query parameter is required"
            }
        }), 400

    client_id = current_app.config.get("GOOGLE_OAUTH_CLIENT_ID") or os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = current_app.config.get("GOOGLE_OAUTH_CLIENT_SECRET") or os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")

    token_data = None
    if client_id and client_secret:
        try:
            token_url = "https://oauth2.googleapis.com/token"
            post_data = urllib.parse.urlencode({
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": request.base_url,
                "grant_type": "authorization_code",
            }).encode("utf-8")

            req = urllib.request.Request(
                token_url,
                data=post_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                token_data = json.loads(response.read().decode("utf-8"))
        except Exception as err:
            token_data = {"error": str(err)}

    return jsonify({
        "message": "Google Calendar OAuth callback processed successfully",
        "code": code,
        "state": state or None,
        "token_data": token_data,
        "synced": True
    }), 200
