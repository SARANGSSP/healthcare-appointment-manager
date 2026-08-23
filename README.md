# Healthcare Appointment & Follow-up Manager

Status: **Chunk 1 — Repo Scaffold & Environment** (Stage A, Build Plan §Chunk 1)

This README covers only what exists right now: an empty API and an
empty web page, both runnable locally and deployable to a public URL.
The full README (setup guide, API docs, DB schema, LLM prompts,
Google Calendar setup) is assembled in Chunk 22 as each piece lands.

## Structure

```
backend/          Flask API + Celery worker, same codebase, two entry points
  app/
    __init__.py    Flask app factory
    config.py      Env-driven config
    celery_app.py  Shared Celery factory (used by worker.py)
    routes/
      health.py    GET /api/v1/health
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
cp ../.env.example .env      # then trim to what Chunk 1 needs, see below
python wsgi.py                # -> http://localhost:5000/api/v1/health
```

For Chunk 1 the backend only reads `FLASK_ENV`, `SECRET_KEY`, and
`CORS_ORIGINS` — the rest of `.env.example` (DB, Redis, LLM, email,
calendar) is reserved for later chunks and safe to leave blank.

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

- [ ] `GET /api/v1/health` returns `{"status": "ok", ...}` locally
- [ ] Same endpoint responds on the deployed Render/Railway URL
- [ ] `web/` home page loads locally and on the deployed Vercel URL
- [ ] Deployed web page's "API status" shows `connected` once
      `NEXT_PUBLIC_API_URL` points at the live API
