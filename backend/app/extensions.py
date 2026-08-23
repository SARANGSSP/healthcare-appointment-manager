"""
Flask extensions, instantiated once and bound to the app in
create_app(). Kept separate from app/__init__.py so model modules
can `from app.extensions import db` without a circular import.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()
