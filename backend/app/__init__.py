"""
Flask application factory.

Started deliberately thin for Chunk 1 (Repo Scaffold & Environment):
no DB, no auth, no business logic — just enough to prove the process
boots, reads config from the environment, and responds on a public
URL. Chunk 3 adds the auth blueprint (register/login/refresh) plus a
role-protected doctors stub; later chunks register their own
blueprints here the same way.
"""
from flask import Flask
from flask_cors import CORS

from app.config import get_config
from app.extensions import db, migrate


def create_app(config_object=None):
    app = Flask(__name__)
    app.config.from_object(config_object or get_config())

    # Permissive CORS for local/dev; tighten to the deployed web
    # origin via CORS_ORIGINS once the frontend URL is known.
    CORS(app, origins=app.config.get("CORS_ORIGINS", "*"))

    db.init_app(app)
    migrate.init_app(app, db)

    # Import models so Alembic's autogenerate can see them (they
    # register themselves on db.Model.metadata as a side effect of
    # being imported) — see app/models/__init__.py.
    from app import models  # noqa: F401

    from app.routes.health import health_bp
    from app.routes.auth import auth_bp
    from app.routes.doctors import doctors_bp
    from app.routes.appointments import appointments_bp

    app.register_blueprint(health_bp, url_prefix="/api/v1")
    app.register_blueprint(auth_bp, url_prefix="/api/v1")
    app.register_blueprint(doctors_bp, url_prefix="/api/v1")
    app.register_blueprint(appointments_bp, url_prefix="/api/v1")

    return app

