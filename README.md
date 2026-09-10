# FinPilot AI

An AI-driven personal finance platform: spending analysis, forecasting, and grounded AI
advice, built as a final-year engineering capstone.

Multi-tenant with Google sign-in. Every table is scoped by `user_id`, every route
(except `/api/auth/*` and `/health`) requires a valid session, and every query is
filtered to the authenticated user via a `get_current_user` dependency rather than a
convention someone has to remember. Read-only access to your name, email, and profile
picture only — never Gmail, Drive, or any bank account, and FinPilot can never move
money.

Monorepo: [`backend/`](backend) (FastAPI) and [`frontend/`](frontend) (React + Vite).

## What's here

- **Data in**: CSV/bank-statement upload with column mapping + preview, manual entry,
  dedup on re-upload, and a rules-then-ML auto-categorizer that learns from your
  corrections
- **Analysis**: monthly/category breakdowns, trend detection vs a 3-month rolling
  average, anomaly detection, budget adherence, savings rate — all pure functions in
  [`backend/app/analysis/`](backend/app/analysis), independently unit tested
- **Forecasting**: Prophet (primary) with an ARIMA baseline for comparison, a
  low-confidence average fallback under 3 months of history, and prediction intervals
  throughout
- **AI recommendations**: Claude-generated advice grounded only in your real numbers,
  schema-validated, cached per data-version, and never able to break the dashboard if the
  API is unavailable
- **Budgets & goals**: monthly limits with live progress/overspend flags; savings goals
  with a projected completion date based on your actual recent savings rate
- **What-if simulator**: per-category sliders with instant client-side projections
  (revised spend, savings rate, months-to-goal), plus an optional AI commentary call
- **Reports**: monthly summary view, CSV export of transactions, PDF export of the
  monthly summary with a chart

## Prerequisites

- Python 3.11+ (developed against 3.14 here, including Prophet — it installed and ran
  cleanly, but if you're on an older Python this is untested territory in the other
  direction)
- Node 20+
- Postgres 16 (optional — SQLite is the zero-config local default)
- An [Anthropic API key](https://console.anthropic.com/) for the AI panel (optional —
  the rest of the app works without it; the AI panel just shows a "temporarily
  unavailable" state)
- A [Google OAuth Client ID](https://console.cloud.google.com/apis/credentials) (Web
  application type) — required to sign in at all. Add `http://localhost:5173` as an
  authorized JavaScript origin for local dev.

## Backend setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# then fill in GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and JWT_SECRET (e.g. `openssl rand -hex 32`)
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

The API is now at `http://localhost:8000` (`/health` for a liveness check, `/docs` for
the interactive Swagger UI). System categories (Food, Rent, Transport, …) are seeded
automatically on startup.

Every route except `/health` and `/api/auth/*` requires a signed-in session, so seeded
demo data sits unowned (`user_id = NULL`) until someone actually signs in — the first
Google sign-in ever claims all of it automatically.

Seed ~12 months of realistic synthetic transactions so the dashboard isn't empty:

```bash
python -m scripts.seed_demo_data          # skips if transactions already exist
python -m scripts.seed_demo_data --reset  # wipes and reseeds
```

By default `DATABASE_URL` in `.env` points at a local SQLite file — no extra setup
needed. To use Postgres instead:

```bash
docker compose up -d postgres
pip install psycopg2-binary
# then set in backend/.env:
# DATABASE_URL=postgresql+psycopg2://finpilot:finpilot@localhost:5432/finpilot
alembic upgrade head
```

Run the test suite:

```bash
source venv/bin/activate
python3 -m pytest
```

## Frontend setup

```bash
cd frontend
npm install
cp .env.example .env
# then set VITE_GOOGLE_CLIENT_ID to the same client ID as the backend's GOOGLE_CLIENT_ID
npm run dev
```

The app is now at `http://localhost:5173`. `/` is the public landing page; every app
route (`/dashboard`, `/import`, …) requires signing in with Google first.

## Repo layout

```
backend/
  app/
    analysis/       # pure functions: trends, anomalies, budgets, savings — no DB calls
    forecasting/     # Prophet + ARIMA + cold-start fallback
    ai/              # Claude prompt, schema, recommendation orchestration + caching
    categorization/  # keyword rules + scikit-learn classifier
    ingestion/       # CSV parsing, column-mapping, dedup, upload staging
    reports/         # CSV/PDF export, monthly summary
    routers/         # FastAPI endpoints
    models/          # SQLAlchemy models (no users table)
  alembic/           # migrations
  scripts/           # seed_demo_data.py
  tests/
frontend/
  src/
    pages/           # Dashboard, Transactions, Budgets, Goals, WhatIf, Reports
    components/      # Layout, charts, AI panel, upload modal, stat tiles
    lib/              # API client, types, money/date formatting, currency context
```

## Design notes

- **Money**: stored as signed integers in the smallest currency unit (paise for the
  default INR), never floats. Currency is a setting (`DEFAULT_CURRENCY`), not hardcoded.
- **Theme**: light-only by design — warm off-white base, white cards lifted with soft
  shadows (not borders), one accent color (emerald) used sparingly for key figures and
  the primary CTA, a tinted-gradient surface for the AI panel to set it apart from the
  data cards.
- **AI outages degrade, never break**: `backend/app/ai/recommendations.py` retries once
  on a schema failure, then falls back to a static "temporarily unavailable" response —
  charts and the rest of the dashboard render regardless of the Claude API's health.
- **CSV parsing defaults to DD/MM/YYYY** (the default locale is INR/India) before falling
  back to MM/DD, since bank exports here are overwhelmingly day-first.
- Secrets live in `.env` (gitignored); only `.env.example` files are committed. The
  Anthropic API key is the only secret in the whole app.

## Deploying (Render + Netlify)

Netlify hosts the static frontend build; it can't run the FastAPI backend (Prophet/
pandas/scikit-learn are too heavy for serverless functions), so the backend needs a real
server — this repo is set up for Render, but any Python host works.

### Backend on Render

Either use the included [`render.yaml`](render.yaml) blueprint (**New → Blueprint**,
point it at this repo — it provisions the web service and a free Postgres database
together), or configure a Web Service by hand:

- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Environment variables: `DATABASE_URL` (Render's Postgres connection string —
  `postgresql://...` works as-is, psycopg2 is the default driver), `APP_ENV=production`,
  `DEFAULT_CURRENCY=INR`,
  `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL=claude-sonnet-4-6`, `MAX_CSV_UPLOAD_MB=5`,
  `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `JWT_SECRET` (`openssl rand -hex 32`),
  `FRONTEND_URL` set to your Netlify URL, and `CORS_ORIGINS` set to a JSON array
  containing that same URL, e.g. `["https://your-site.netlify.app"]`. Remember to add
  your Render URL as an authorized JavaScript origin on the Google OAuth client too.

Once it's live, seed demo data via Render's Shell tab: `python -m scripts.seed_demo_data`.

### Frontend on Netlify

[`netlify.toml`](netlify.toml) at the repo root already points Netlify at `frontend/`,
builds with `npm run build`, publishes `dist/`, and redirects all paths to `index.html`
for React Router. In the Netlify dashboard:

- **Add new site → Import an existing project**, pick this repo (base directory/build
  settings are read from `netlify.toml` automatically)
- Set the environment variable `VITE_API_BASE_URL` to your Render backend's URL (e.g.
  `https://finpilot-backend.onrender.com`) — Vite bakes this in at build time, so set it
  *before* the first deploy, or trigger a redeploy after adding it
- Once you have the Netlify URL, go back to Render and update `CORS_ORIGINS` to include
  it, or the browser will block the API calls

Render's free tier spins down on inactivity — the first request after idling can take
10-30 seconds to wake back up.
