from flask import Blueprint, current_app, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    """
    Chunk 1's 'done when': this responds on a public URL with no DB,
    no auth, and no external services wired up yet. Later chunks can
    extend this with a real DB ping once Chunk 2 lands.
    """
    return jsonify(
        {
            "status": "ok",
            "service": "healthcare-appointment-manager-api",
            "env": current_app.config.get("ENV", "unknown"),
        }
    )
