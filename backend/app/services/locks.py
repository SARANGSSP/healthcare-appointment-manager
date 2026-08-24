"""
Redis lock service module (Design Document §6/§8).
UX-layer Redis NX lock convenience on top of PostgreSQL partial unique index.
Gracefully degrades to DB-only behavior if REDIS_URL is not set or Redis is unreachable.
"""
import os
import redis
from flask import current_app

redis_client = None


def init_redis(app):
    global redis_client
    redis_url = app.config.get("REDIS_URL") or os.environ.get("REDIS_URL")
    if redis_url:
        try:
            client = redis.Redis.from_url(redis_url, decode_responses=True)
            redis_client = client
        except Exception:
            redis_client = None
    else:
        redis_client = None


def acquire_slot_lock(doctor_id: int, date_str: str, slot_start_str: str, request_id: str = "held") -> bool:
    """
    Attempts Redis SET NX lock with 300s TTL (lock:doctor:{id}:{date}:{slot}).
    Returns True if lock acquired or if Redis is unavailable (degrades to DB).
    Returns False if lock is already held in Redis.
    """
    global redis_client
    target_client = redis_client
    if not target_client:
        try:
            redis_url = (current_app.config.get("REDIS_URL") if current_app else None) or os.environ.get("REDIS_URL")
            if redis_url:
                target_client = redis.Redis.from_url(redis_url, decode_responses=True)
        except Exception:
            pass

    if not target_client:
        return True  # Graceful fallback to DB-only behavior

    key = f"lock:doctor:{doctor_id}:{date_str}:{slot_start_str}"
    try:
        acquired = target_client.set(key, request_id, nx=True, ex=300)
        return bool(acquired)
    except Exception:
        return True  # Graceful fallback to DB-only behavior


def release_slot_lock(doctor_id: int, date_str: str, slot_start_str: str):
    """Optional release of slot lock on confirm/cancel/expiry."""
    global redis_client
    target_client = redis_client
    if not target_client:
        try:
            redis_url = (current_app.config.get("REDIS_URL") if current_app else None) or os.environ.get("REDIS_URL")
            if redis_url:
                target_client = redis.Redis.from_url(redis_url, decode_responses=True)
        except Exception:
            pass

    if not target_client:
        return

    key = f"lock:doctor:{doctor_id}:{date_str}:{slot_start_str}"
    try:
        target_client.delete(key)
    except Exception:
        pass
