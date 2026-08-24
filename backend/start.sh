#!/bin/bash
# start.sh: Migrate DB, seed admin, then run Flask + Celery in a single Free-tier container

set -e  # Exit immediately if any command fails

echo "==> Running database migrations..."
flask db upgrade

echo "==> Seeding initial admin user (skipped if already exists)..."
python - <<'EOF'
import os, sys
from app import create_app, db
from app.models.user import User

app = create_app()
with app.app_context():
    if not User.query.filter_by(role='admin').first():
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'changeme123')
        u = User(name='Admin', email=admin_email, role='admin')
        u.set_password(admin_password)
        db.session.add(u)
        db.session.commit()
        print(f"Admin created: {admin_email}")
    else:
        print("Admin already exists, skipping seed.")
EOF

echo "==> Starting Celery worker..."
celery -A worker.celery worker --loglevel=info --concurrency=1 &

echo "==> Starting Celery beat..."
celery -A worker.celery beat --loglevel=info --scheduler celery.beat:PersistentScheduler &

echo "==> Starting Gunicorn..."
exec gunicorn wsgi:app
