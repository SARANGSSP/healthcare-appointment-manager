# Healthcare Appointment & Follow-up Manager

Status: **Chunk 2 — Database Schema & Migrations** (Stage A, Build Plan §Chunk 2)

This README covers only what exists right now. The full README
(setup guide, API docs, DB schema, LLM prompts, Google Calendar
setup) is assembled in Chunk 22 as each piece lands.

## Structure

```
backend/          Flask API + Celery worker, same codebase, two entry points
  app/
    __init__.py    Flask app factory
    config.py      Env-driven config
    extensions.py  Shared db (SQLAlchemy) / migrate (Flask-Migrate) instances
    celery_app.py  Shared Celery factory (used by worker.py)
    models/        One file per table from Design Document §4
      user.py, patient_profile.py, doctor_profile.py, doctor_leave.py,
      appointment.py, symptom_summary.py, visit_note.py,
      prescription_item.py, medication_reminder.py, notification.py,
      calendar_event.py
    routes/
      health.py    GET /api/v1/health
  migrations/      Alembic migration history (Flask-Migrate)
  wsgi.py          API entrypoint
  worker.py        Worker entrypoint
  requirements.txt
  Procfile

web/               Next.js app (App Router)
  app/
    layout.tsx
    page.tsx       Placeholder home page, pings API health check

.env.example       Every env var the whole project will need
render.yaml        Render Blueprint: api + worker + Postgres + Redis
```

## Local setup

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env      # trim to what's needed so far, see below

# Provision a local Postgres database matching DATABASE_URL, e.g.:
#   createdb healthcare_appt

flask db upgrade               # applies migrations/versions/*.py
python wsgi.py                 # -> http://localhost:5000/api/v1/health
```

As of Chunk 2 the backend reads `FLASK_ENV`, `SECRET_KEY`,
`CORS_ORIGINS`, and `DATABASE_URL`. The rest of `.env.example`
(Redis, LLM, email, calendar) is reserved for later chunks and safe
to leave blank.

To generate a new migration after changing a model:

```bash
flask db migrate -m "describe the change"
flask db upgrade
```

### Frontend

```bash
cd web
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:5000" > .env.local
npm run dev                   # -> http://localhost:3000
```

## Hosted deployment

- **Web → Vercel**: import the repo, set the project root to `web/`,
  add `NEXT_PUBLIC_API_URL` pointing at the deployed API.
- **API + worker → Render**: use the included `render.yaml` Blueprint
  (New → Blueprint → select this repo). It provisions the API web
  service, the worker as a separate always-on service, a managed
  Postgres instance, and a managed Redis instance.
  - Railway is an equally valid alternative to Render if preferred —
    create two services from `backend/` (one running
    `gunicorn wsgi:app`, one running `celery -A worker.celery worker`)
    plus managed Postgres and Redis add-ons.
- Confirm whichever host is chosen does **not** sleep/idle the worker
  service on its free tier — a sleeping worker means reminders and
  retries silently stop firing later (Design Document §2.3).

## Done-when check (Chunk 1)

- [x] `GET /api/v1/health` returns `{"status": "ok", ...}` locally
- [ ] Same endpoint responds on the deployed Render/Railway URL
- [ ] `web/` home page loads locally and on the deployed Vercel URL
- [ ] Deployed web page's "API status" shows `connected` once
      `NEXT_PUBLIC_API_URL` points at the live API

## Done-when check (Chunk 2)

- [x] `flask db upgrade` runs clean on a fresh database — all 11
      tables from Design Document §4 created (`user`,
      `patient_profile`, `doctor_profile`, `doctor_leave`,
      `appointment`, `symptom_summary`, `visit_note`,
      `prescription_item`, `medication_reminder`, `notification`,
      `calendar_event`)
- [x] All four §4.1 indexes exist, confirmed via `\d appointment` /
      `\d doctor_leave` / `\d medication_reminder` in psql:
      `idx_appt_no_double_book` (partial, unique), `idx_appt_patient`,
      `idx_leave_doctor_date`, `idx_reminder_due`
- [x] Manual duplicate-insert test in psql: inserting a second
      `confirmed` (or `held`) appointment for the same
      `(doctor_id, appt_date, slot_start)` throws a unique-violation;
      the same slot becomes bookable again once the original row's
      status is no longer `held`/`confirmed` (e.g. `cancelled`) —
      confirming the index is genuinely partial, not blanket-unique
- [x] `flask db downgrade` cleanly drops everything back to empty
      and `flask db upgrade` re-creates it — the migration is
      reversible, not just forward-only
