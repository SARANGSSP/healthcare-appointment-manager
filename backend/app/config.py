"""
All configuration comes from the environment (.env locally, real
env vars on Render/Railway) so local and hosted deployments stay
in parity from Chunk 1 onward — see SDP §2, "Environment parity".

Nothing here is consumed yet except CORS_ORIGINS; DATABASE_URL /
REDIS_URL / API keys are wired in Chunks 2, 8, 12, 14, 15 as the
matching module lands. They're declared now so .env.example is the
single source of truth for every variable the project will ever need.
"""
import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    ENV = os.environ.get("FLASK_ENV", "development")
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # Comma-separated list of allowed origins, e.g.
    # "http://localhost:3000,https://your-app.vercel.app"
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")

    # --- Database (Chunk 2) ---
    DATABASE_URL = os.environ.get(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/healthcare_appt"
    )
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Auth (Chunk 3) ---
    JWT_SECRET = os.environ.get("JWT_SECRET")
    JWT_ACCESS_TOKEN_EXPIRES_MINUTES = os.environ.get("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "15")
    JWT_REFRESH_TOKEN_EXPIRES_DAYS = os.environ.get("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "7")

    # --- Reserved for upcoming chunks (see .env.example) ---
    REDIS_URL = os.environ.get("REDIS_URL")
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
    SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
    GOOGLE_OAUTH_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
    GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
    GOOGLE_OAUTH_REDIRECT_URI = os.environ.get("GOOGLE_OAUTH_REDIRECT_URI")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


def get_config():
    env = os.environ.get("FLASK_ENV", "development")
    return ProductionConfig if env == "production" else DevelopmentConfig
