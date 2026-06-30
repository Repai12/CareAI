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
 
- **Backend:** Python 3.11 · FastAPI (async REST API)
- **Frontend:** Next.js 14 (App Router) · React 18 · TypeScript · Tailwind CSS
- **Database:** PostgreSQL · SQLAlchemy 2 · Alembic migrations
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
 
## Getting Started
 
```bash
# Clone the repo
git clone <repo-url>
cd careai
 
# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
 
# Frontend setup
cd ../frontend
npm install
npm run dev
```
 
### Environment Variables
 
See `.env.example` in both `backend/` and `frontend/` for required configuration (database URL, JWT secret, Groq API key, Twilio credentials).
 
## License
 
This project was developed for academic purposes as part of CSE471.
 
