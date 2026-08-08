
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
 
main
## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
