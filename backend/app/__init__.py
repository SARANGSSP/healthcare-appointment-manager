"""
Flask application factory.

Kept deliberately thin for Chunk 1 (Repo Scaffold & Environment):
no DB, no auth, no business logic yet — just enough to prove the
process boots, reads config from the environment, and responds on
a public URL. Everything else (blueprints for auth, doctors,
appointments, etc.) gets registered here in later chunks.
"""
from flask import Flask
from flask_cors import CORS

from app.config import get_config


def create_app(config_object=None):
    app = Flask(__name__)
    app.config.from_object(config_object or get_config())

    # Permissive CORS for local/dev; tighten to the deployed web
    # origin via CORS_ORIGINS once the frontend URL is known.
    CORS(app, origins=app.config.get("CORS_ORIGINS", "*"))

    from app.routes.health import health_bp

    app.register_blueprint(health_bp, url_prefix="/api/v1")

    return app
