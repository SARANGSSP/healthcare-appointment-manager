#!/bin/bash
# start.sh: Run Flask, Celery Worker, and Celery Beat in a single container (Render Free Plan)

# Start Celery worker in background (concurrency=1 to stay within the 512MB RAM free tier limit)
celery -A worker.celery worker --loglevel=info --concurrency=1 &

# Start Celery Beat in background
celery -A worker.celery beat --loglevel=info --scheduler celery.beat:PersistentScheduler &

# Start Flask via Gunicorn in foreground
gunicorn wsgi:app
