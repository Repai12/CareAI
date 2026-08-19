
#CareAI 🩺
 
**AI-powered elderly health monitoring platform** that connects elderly patients, their families, and doctors in one place — helping families stay informed and helping patients stay safe, without constant phone calls or check-in visits.
 
## Overview
 
CareAI is a full-stack web application built for **CSE471: System Analysis and Design**. It addresses a real problem: families living apart from elderly relatives often have no visibility into their day-to-day health, and doctors only see patients during scheduled visits. CareAI bridges that gap with shared, role-based access to health data, real-time communication, and AI-assisted tools.
 
The platform supports three roles:
- 👵 **Elderly Patient** — logs medication, mood, meals, and activity; chats with an AI companion; triggers SOS in emergencies
- 👨‍👩‍👧 **Family Member** — monitors compliance and wellbeing, receives emergency alerts, communicates via family chat
- 🩺 **Doctor** — manages medical records, uses AI to analyze reports, answers patient-history questions
## Features
 
| Module | Highlights |
|---|---|
| **Module 1** | Activity tracking with trend dashboards, medical visit & records management, mood tracking, doctor diagnosis entries |
| **Module 2** | Medication scheduler with compliance tracking, nutrition planner, wellness recommendation engine, AI medical report analyzer |
| **Module 3** | Severity-based incident/fall alerting, AI weekly health summaries, AI prescription summarizer, family chat, dual-persona AI companion, emergency SOS with escalation, AI patient history Q&A, automated daily digest |
 
## Tech Stack
 
- **Backend:** FastAPI 
- **Frontend:** Next.js
- **Database:** PostgreSQL
- **AI:** Groq API (Llama 3.3 70B) — used for summaries, reflections, AI companion chat, and Q&A
- **Notifications:** Twilio (SMS-based SOS alerts)
- **Real-time:** WebSockets (family/doctor chat)
- **Auth:** JWT (python-jose) + bcrypt
- **Deployment:** Vercel (frontend) · Render (backend + PostgreSQL)
## Why This Stack
 
We intentionally avoided heavy computer-vision AI (fall detection from video, food recognition from photos) in favor of lightweight, reliable text-based AI calls through a single provider (Groq), reused across every AI feature. This keeps the project realistic to build well within a semester while still demonstrating genuine AI integration, relational database design, and real-time features.
 
## Team
 
| Name | Student ID |
|---|---|
| Mubasshira Abtahi | 22201717 |
| Afifa Tanjeem Adiba | 22101716 |
| Md. Faisal Bhuiyan | 23101077 |
| Repai Ul Islam | 23101084 |
 
Each team member owns a complete vertical slice of features — database schema, backend endpoints, and frontend UI — across the project's three modules.

## Getting Started (local setup, from a fresh clone)

Follow these steps in order. They assume **Python 3.11 or 3.12** (not 3.13+ — some pinned backend dependencies don't yet ship prebuilt wheels for newer Pythons, which means pip tries to compile them from source and fails unless you have a Rust/C++ toolchain installed), Node 18+, and git.

### 1. Clone and enter the repo

```bash
git clone https://github.com/Repai12/CareAI.git
cd CareAI
```

### 2. Backend setup

```bash
cd backend
python -m venv venv
```

If your default `python` is 3.13+, create the venv with a specific version instead, e.g. `py -3.12 -m venv venv` (Windows) or `python3.12 -m venv venv` (macOS/Linux).

Activate the virtual environment:
- macOS/Linux: `source venv/bin/activate`
- Windows (PowerShell): `venv\Scripts\Activate.ps1`

```bash
pip install -r requirements.txt
```

Copy the example env file and fill in real values:

```bash
cp .env.example .env
```

At minimum, set `DATABASE_URL` to the team's shared Neon connection string (ask a teammate, or see "Working with a shared database" below). `RESEND_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`, and the `TWILIO_*` variables can be left blank locally — the features that need them will fail gracefully and log a warning instead of crashing, but you'll want real keys to actually test those features.

Apply the database schema:

```bash
alembic upgrade head
```

(Optional) Seed demo data so the dashboard has something to show:

```bash
python seed_demo_data.py
```

This is safe to run once against an empty/fresh set of demo rows — it checks for the demo patient (`patient@demo.com`) first and exits without changes if that data already exists, so it will not duplicate rows if you (or a teammate) already ran it against the shared database.

Start the backend:

```bash
uvicorn app.main:app --reload
```

The API is now running at `http://localhost:8000`.

### 3. Frontend setup

In a second terminal:

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). `.env.local` only needs editing if your backend isn't running on `localhost:8000`.

### Working with a shared database

The team shares one Neon PostgreSQL database. A few rules to avoid collisions:

- **Never run `seed_demo_data.py` more than once against it** — it already guards against duplicate demo rows, but it is not a substitute for each teammate creating their own real test accounts through the app's normal registration flow for anything beyond the fixed demo patient/family/doctor trio.
- **Run `alembic upgrade head` before you start working**, and whenever you pull new commits — someone else may have added a migration. Never hand-edit the shared schema outside of a migration file.
- **If you need a new table or column**, write an Alembic migration (`alembic revision --autogenerate -m "..."`) rather than editing the database directly — otherwise everyone else's local schema drifts out of sync with yours.
- Each teammate's `backend/.env` should point at the same `DATABASE_URL` — get it from whoever set up the Neon project, or from the Neon console's "Connect" dialog if you have access.

## Deployment

- **Frontend:** Vercel
- **Backend + PostgreSQL:** Render / Neon
