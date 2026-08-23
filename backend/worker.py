"""
Worker process entrypoint — same codebase as the API (see wsgi.py),
different entry point, per SDP §2 / Design Document §2.3.

Local:    celery -A worker.celery worker --loglevel=info
Hosted:   same command, as a separate Render/Railway service so it
          stays running continuously rather than scaling to zero
          (Design Document §2.3 — a sleeping worker means reminders
          and retries silently stop firing).

No real tasks are registered yet. Chunk 12 adds the first one
(pre-visit LLM summary job); Chunks 14-16 add email, calendar, and
reminder tasks on top of the same Celery instance.
"""
from app import create_app
from app.celery_app import create_celery

flask_app = create_app()
celery = create_celery(flask_app)
