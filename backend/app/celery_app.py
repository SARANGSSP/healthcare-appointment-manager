"""
Celery factory shared between the API and worker processes.

Design Document §2.3: same codebase, two deployable entry points
(wsgi.py for the API, worker.py for the worker). Binding Celery to
the Flask app context here — rather than building it standalone —
means tasks added in later chunks (email, calendar, LLM jobs) can
use app.config and Flask extensions without re-wiring anything.

H1/H3/H8 fix: beat_schedule now registers three periodic tasks:
  - sweep-expired-holds     → every 30 s  (H8)
  - retry-failed-notifs     → every 60 s  (H3)
  (LLM tasks are triggered on-demand via .delay(), not beat)
"""
from celery import Celery
from celery.schedules import crontab


def create_celery(app):
    celery = Celery(
        app.import_name,
        broker=app.config.get("REDIS_URL", "redis://localhost:6379/0"),
        backend=app.config.get("REDIS_URL", "redis://localhost:6379/0"),
    )
    celery.conf.update(app.config)

    # Auto-discover tasks in app/tasks.py
    celery.autodiscover_tasks(["app"])

    # H8 / H3: periodic beat schedule
    celery.conf.beat_schedule = {
        "sweep-expired-holds": {
            "task": "tasks.sweep_expired_holds_task",
            "schedule": 30.0,  # every 30 seconds
        },
        "retry-failed-notifications": {
            "task": "tasks.retry_notifications_task",
            "schedule": 60.0,  # every 60 seconds
        },
    }
    celery.conf.timezone = "UTC"

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
