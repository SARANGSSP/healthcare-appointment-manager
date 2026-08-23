"""
JWT + refresh token issuance (Build Plan Chunk 3 / Design Document §5).

Stateless refresh tokens: a refresh token is just a longer-lived JWT
with type='refresh', so /auth/refresh doesn't need a database table
to look anything up. This is deliberately the simplest thing that
satisfies the brief; if the project later needs server-side revocation
(logout-everywhere, stolen-token invalidation), a refresh_token table
keyed by jti would replace this without touching callers of
create_access_token / create_refresh_token.
"""
import time

import jwt
from flask import current_app

ALGORITHM = "HS256"


def _secret():
    return current_app.config.get("JWT_SECRET") or current_app.config["SECRET_KEY"]


def _encode(payload, expires_in_seconds):
    now = int(time.time())
    full_payload = {**payload, "iat": now, "exp": now + expires_in_seconds}
    return jwt.encode(full_payload, _secret(), algorithm=ALGORITHM)


def create_access_token(user):
    minutes = int(current_app.config.get("JWT_ACCESS_TOKEN_EXPIRES_MINUTES") or 15)
    return _encode(
        {"sub": str(user.id), "role": user.role, "type": "access"},
        minutes * 60,
    )


def create_refresh_token(user):
    days = int(current_app.config.get("JWT_REFRESH_TOKEN_EXPIRES_DAYS") or 7)
    return _encode(
        {"sub": str(user.id), "role": user.role, "type": "refresh"},
        days * 24 * 60 * 60,
    )


def decode_token(token):
    """Raises jwt.ExpiredSignatureError / jwt.InvalidTokenError on failure."""
    return jwt.decode(token, _secret(), algorithms=[ALGORITHM])
