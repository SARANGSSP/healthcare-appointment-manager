"""
Celery factory shared between the API and worker processes.

Design Document §2.3: same codebase, two deployable entry points
(wsgi.py for the API, worker.py for the worker). Binding Celery to
the Flask app context here — rather than building it standalone —
means tasks added in later chunks (email, calendar, LLM jobs) can
use app.config and Flask extensions without re-wiring anything.

No real tasks yet: Chunk 12 (Stage D) is the first chunk that
actually needs the queue, at which point this becomes the shared
broker/backend for Reminder, Email Retry, and Calendar Sync workers
(Design Document §2.2).
"""
from celery import Celery


def create_celery(app):
    celery = Celery(
        app.import_name,
        broker=app.config.get("REDIS_URL", "redis://localhost:6379/0"),
        backend=app.config.get("REDIS_URL", "redis://localhost:6379/0"),
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
