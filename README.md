# Healthcare Appointment & Follow-up Manager

Status: **Chunk 5 — Doctor & Admin Profile Management** (Stage B, Build Plan §Chunk 5)

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
    auth/
      tokens.py      JWT access/refresh token issuance + decoding
      decorators.py  @login_required / @role_required route middleware
    models/        One file per table from Design Document §4
      user.py, patient_profile.py, doctor_profile.py, doctor_leave.py,
      appointment.py, symptom_summary.py, visit_note.py,
      prescription_item.py, medication_reminder.py, notification.py,
      calendar_event.py
    routes/
      health.py    GET /api/v1/health
      auth.py      POST /auth/register, /auth/login, /auth/refresh, GET /auth/me
      doctors.py   GET /doctors/me — role-protected stub proving the
                   middleware; Chunk 5 replaces this with real CRUD
  migrations/      Alembic migration history (Flask-Migrate)
  wsgi.py          API entrypoint
  worker.py        Worker entrypoint
  requirements.txt
  Procfile

web/               Next.js app (App Router)
  app/
    layout.tsx        Imports styles/globals.css + Design Document §2.2 fonts
    page.tsx           Placeholder home page, pings API health check, links to auth
    login/page.tsx      Restyled in Chunk 4 with the shared component library
    register/page.tsx
    patient/page.tsx  Role-gated home screens, now wrapped in AppShell —
    doctor/page.tsx   real content lands with each portal's later chunk
    admin/page.tsx    (Frontend Design Document §3)
    styleguide/page.tsx  Chunk 4 "done when": every component, every state,
                         no real data — visit directly at /styleguide
  components/
    ui/    Button, Input, TextArea, Card, Table, Badge (+ Urgency/Status
           wrappers), Toast, VitalsLine — Frontend Design Document §5
    shell/ AppShell.tsx — shared shell + per-portal nav (§3.1-§3.3)
  styles/
    tokens.css   Color/type/spacing/radius/motion CSS variables (§2)
    globals.css  Resets + component classes consumed by components/ui
  lib/
    api.ts            Auth API client + session (token) storage
    useRequireRole.ts  Redirects to /login on missing/mismatched role

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

As of Chunk 3 the backend reads `FLASK_ENV`, `SECRET_KEY`,
`CORS_ORIGINS`, `DATABASE_URL`, `JWT_SECRET`,
`JWT_ACCESS_TOKEN_EXPIRES_MINUTES`, and
`JWT_REFRESH_TOKEN_EXPIRES_DAYS`. Set a real `JWT_SECRET` locally too
(the app falls back to `SECRET_KEY` if it's blank, but don't rely on
that in anything shared). The rest of `.env.example` (Redis, LLM,
email, calendar) is reserved for later chunks and safe to leave blank.

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

## Done-when check (Chunk 3)

- [x] `POST /api/v1/auth/register` with `role: "patient"` creates a
      `user` row (bcrypt-hashed password) + matching
      `patient_profile` row, and returns an access + refresh token
- [x] Registering with `role: "doctor"` creates a `doctor_profile`
      row instead; `role: "admin"` creates no profile row at all
      (Design Document §4 — admin is a bare role)
- [x] `POST /api/v1/auth/login` with the same credentials returns a
      fresh access + refresh token pair; wrong password returns 401
      with the standard `{ error: { code, message, details } }` shape
- [x] `POST /api/v1/auth/refresh` exchanges a valid refresh token for
      a new access token without re-entering a password
- [x] `GET /api/v1/auth/me` returns the current user with a valid
      access token, and 401s with no token / an expired token
- [x] `GET /api/v1/doctors/me` (the Chunk 3 role-middleware proof
      route) returns 200 for a doctor's access token and 403 for a
      patient's or admin's — confirms `@role_required` actually
      blocks cross-role access, not just documents an intent
- [x] In the browser: registering as a patient lands on `/patient`;
      registering as a doctor lands on `/doctor`; logging in
      redirects the same way — role-aware redirect confirmed for all
      three roles, not just patient
- [x] Visiting `/doctor` or `/admin` directly without a session (or
      with a patient session) redirects to `/login` rather than
      rendering the page

## Done-when check (Chunk 4)

- [x] `/styleguide` renders every base component (Button, Input,
      TextArea, Card, Table, Badge, Toast, VitalsLine) in every state
      listed in Frontend Design Document §5, with no real/fetched
      data behind it
- [x] Color, type, and spacing tokens from §2 are wired as CSS
      variables in `web/styles/tokens.css`, consumed by every
      component in `web/styles/globals.css` — no hard-coded hex
      values in component files
- [x] The vitals-line SVG divider renders standalone (static, all
      four status tones) and with the one-shot draw-in animation,
      and respects `prefers-reduced-motion` (§2.5)
- [x] `AppShell` renders a role-aware nav for all three portals
      (Patient/Doctor/Admin) with the correct IA per §3.1-§3.3; the
      patient portal renders narrower/linear per §3.1, Doctor/Admin
      render full-width
- [x] Login, register, and all three portal home screens (built in
      Chunk 3) are restyled through the shared component library —
      no screen still uses ad hoc inline styles from before Chunk 4
- [x] `npx tsc --noEmit` and `next build` both pass clean with the
      new components in place

## Done-when check (Chunk 5)

- [x] Admin CRUD REST endpoints (`GET /doctors`, `GET /doctors/<id>`, `POST /doctors`, `PUT /doctors/<id>`, `DELETE /doctors/<id>`) implemented with role authorization (`@role_required("admin")`).
- [x] Patient tokens attempt to mutate doctor profiles are blocked with `403 Forbidden`.
- [x] An admin can view all doctor profiles in the Doctors Data Table on `/admin`.
- [x] An admin can create a doctor profile through the UI form (creating user account & doctor profile) and see it appear in the table.
- [x] An admin can edit full name, specialisation, email, and slot duration via the Edit Doctor modal.
- [x] An admin can delete a doctor profile with confirm dialog, cleanly cascading to user account.

