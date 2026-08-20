# CareAI Audit

## Progress log (2026-08-20)

**Scope note (2026-08-20, later same day):** everything above this line audited the codebase
against README's numbered spec sections, but never checked the top-level **Features** table
itself feature-by-feature. Doing that turned up five README-listed features with **zero code,
backend or frontend** - not broken, never started: mood tracking, AI prescription summarizer, AI
patient history Q&A, dual-persona AI companion, and family chat over WebSockets. Building all
five now, each its own entry below. ("Doctor diagnosis entries", also listed, turns out to
already be covered by `VisitNote.notes` - not a real gap.)

14. **Mood tracking** (Module 1) - built from scratch: `MoodLog` model/migration, `routers/mood.py`
    (`POST`/`GET /mood/{patient_id}`, patient logs, patient+active-linked family/doctor view),
    and a new Mood tab in the Health module (emoji picker + note + 14-day trend dots + history).
    Verified live: patient logs a mood with a note, entry appears immediately with the correct
    trend dot and timestamp; logging back in as the linked family account on the same URL shows
    the same history read-only with the picker correctly hidden (`isOwner` gate). Multiple
    entries/day allowed on purpose - a real user checks in more than once.

15. **AI Prescription Summarizer** (Module 3) - extends the existing Visit Notes feature rather
    than duplicating it: added a cached `ai_summary` column to `visit_notes`, a new `POST
    /visit-notes/{patient_id}/{visit_note_id}/summarize` endpoint (patient + active-linked
    family/doctor, not doctor-only - this is for the layperson audience), and a
    `summarize_prescription()` helper reusing `groq_health_service.py`'s existing Groq client. An
    "Explain in plain English" button appears on every visit note; the summary is generated once
    and cached, not regenerated on every page view. Verified live against the real (keyless) dev
    environment: clicking the button surfaces "AI explanation is temporarily unavailable" via a
    503, not a crash, and the button stays clickable for a retry rather than caching a null
    result - confirms the graceful-degradation path works even though the happy path (an actual
    Groq key) is untested here, same limitation as the AI Symptom Checker/Diet Advisor before it.


Fixed and verified live (real DB + real browser sessions), on branch `fix/stabilize-and-polish`:

1. **Environment & boot** (`849e3aa`) — added `.env.example` for both apps, fixed `requirements.txt`
   (missing `alembic`), rewrote the one Alembic migration (was ALTER statements against a schema
   that only existed on one dev's machine — crashed on any empty DB), fixed `seed_demo_data.py`
   (referenced fields removed in a prior migration) and gave it a re-run guard, rewrote the README
   setup section with real steps. Fresh clone → `alembic upgrade head` → `uvicorn` → `next dev` now
   all work.
2. **Auth & sessions** (`83dd871`) — email verification, password reset, refresh-token sessions
   (access token in memory, not localStorage; httpOnly refresh cookie; rotation; revocation;
   "logout everywhere"), login rate limiting, doctor-unverified badge. Matches README S3 in full.
3. **Connections system** (`83dd871`) — `patient_links` → `care_links` with the full README S4 model
   (status, permission_level, invited_by, timestamps, real FKs). Registering with a patient_code now
   creates a *pending* link and notifies the patient instead of granting instant access. Added
   approve/decline/revoke/permission endpoints and a minimal `/connections` page so patients can
   actually act on requests.

**Process note:** commit `579f4b7` ("Fix auth & session gaps") originally under-staged — a `git add`
with one bad pathspec silently aborted, and the follow-up `git status` was misread, so most of that
work sat uncommitted for a while. Nothing was lost; it was folded into `83dd871` with an honest
description of what happened. Staging file-by-file (no wildcards) going forward to avoid a repeat.

4. **SOS, Fall Logger, Daily Check-in** (`385ca49`) — SOS had a UUID/int type bug (delete never
   worked), 400'd with zero contacts instead of still logging+notifying, and sent SMS as one
   all-or-nothing batch. Fall Logger and Daily Check-in had DB models but were 100% unreachable —
   the one file attempting the logic imported a class that didn't exist where it claimed and was
   never called from anywhere. Built real routers for both, wired the missed-check-in job into the
   scheduler (runs daily, was never registered).
5. **Medications + Appointments + Calendar** (`4e5a48a`, `3b90494`) — medications had no `patient_id`
   (dashboard hardcoded to `[]`); the dead `appointments.py` router had **zero authentication**
   (any token could read every patient's appointments); Calendar sync failure rolled back the whole
   booking instead of degrading gracefully, the opposite of the README requirement. Fixed all three,
   wired appointments.py + calendar.py into main.py, added the missing frontend page.

6. **Medicine Adherence Tracker + Doctor Visit Notes** (`1c3ee43`, `85f7498`) — same story as
   appointments: dead routers with zero auth, referencing `MedicationLog`/`VisitNote` model classes
   that were never defined anywhere (`crud.py` even had a second, equally dead, unused duplicate
   implementation). Built real models + migration, real auth (doctor-only writes, only the authoring
   doctor can edit/archive their own note), the "3 consecutive misses, not every miss" notification
   nuance from README S8.4, and frontend for both. Also fixed the login page's demo-account
   quick-select buttons, which still pointed at pre-rewrite seed emails and silently failed.

7. **Vitals real-user pass** (`2e6cc23`) — `blood_pressure` had zero validation (the one field README
   S6.1 explicitly calls out by name: "silently accepting '999' as blood pressure isn't graceful
   degradation, it's a broken feature"). Now rejects bad format/range/diastolic-over-systolic before
   the row is written. The rest of Module 1 (vitals CRUD, AI report analyzer, symptom checker, diet
   advisor) was already genuinely solid — real timeouts, graceful AI-failure fallbacks, real
   validation elsewhere — no rewrite needed.
8. **AI disclaimers + urgent-symptom prompt** (`b7c060e`) — README requires "AI-generated, not a
   diagnosis" on every AI-output panel and a visible "this may be urgent" prompt on
   urgent/emergency symptom results; neither existed anywhere in the frontend (confirmed by grep).
   Added both.
9. **Patient list/switcher** (`fbb7900`) — a structural gap, not a bug: `care_links` is genuinely
   many-to-many, but the frontend had no way for a family member or doctor linked to more than one
   patient to ever see or reach the second one — login just redirected to `patients[0]` and stopped.
   Invisible in all testing until now because every demo account only had one linked patient. Added
   a real `/patients` list page and a switcher link.
10. **Safety page** (`4e7a258`) — the single most load-bearing corner case in the app (SOS is useless
    with zero emergency contacts) had no frontend to add a contact at all. Same for the Fall Logger
    and Daily Check-in, both working on the backend since commit `385ca49` but with zero UI. Built
    `/safety/[patientId]` covering all three.

11. **Weekly Email Report hardened end-to-end** (`f5a0736`) — taken to zero known corner cases as a
    deliberate "finish one feature completely" pass. Found and fixed three separate real bugs:
    `send_email()` raised instead of returning `False` when `RESEND_API_KEY` was unset (crashed both
    the weekly report AND the doctor AI summary — same root cause, fixed once in `email_service.py`
    for both); `POST /reports/weekly/trigger` had no ownership check at all (any patient/doctor could
    trigger emails about an unrelated patient — a real IDOR) and `GET /reports/weekly/{id}` had no
    auth check whatsoever; and `ReportPanel.tsx` compared status against lowercase `"sent"` when the
    backend always returns uppercase `"SENT"`/`"FAILED"`, so a successful send silently rendered in
    the failure color. Added a 24h duplicate-send guard (doesn't block retrying failed attempts).

12. **Role-appropriate dashboards + connections polish** (`b44b930`) — the connections mechanism
    itself (care_links, invite/approve) was already solid; this closed the "who sees what" gaps
    around it. `ReportPanel` showed "Send report now" to family, who the backend has always
    rejected with a 403 — hidden now. Patient dashboard had no version of README S5's "no linked
    family/doctor yet" nudge banner — added, verified both the zero-link and has-link cases live.
    The patient's own `patient_code` was only ever shown once at registration with no way to look
    it up again — now persistent on `/connections` with a working copy button. `/patients` (the
    landing page for a family/doctor with 2+ linked patients) was a bare name list — upgraded to
    README S2's actual spec: latest vitals status, unread notification count, next appointment per
    patient, sorted with unread-EMERGENCY patients first. Also fixed two supporting gaps hit along
    the way: `lib/api/notifications.ts` was never in the `lib/api.ts` barrel export, and
    `getMyPatients()`'s frontend type was missing `patient_code` despite the backend returning it.

13. **Site-wide background treatment** (`95d9e68`) — final polish pass. Every page used a flat
    `#F4F7F6` off-white with zero depth. Replaced with a layered gradient + three large, heavily
    blurred, low-opacity color shapes (sage/gold/steel, the existing palette — no new colors)
    defined once in `app/layout.tsx` so it's automatically consistent on every route, including
    pages that never had their own background styling. Removed the flat `bg-paper` override from
    15 individual pages so the new layout-level background actually shows through. No component
    logic touched — purely `globals.css` + `layout.tsx` + className cleanup. Verified visually
    across the landing page, a form page, a fully-loaded dashboard, and a page with no prior
    background styling — card/text legibility holds up in every case.

**Not yet done**: frontend route restructuring (`/patient/*`, `/family/*`, `/doctor/*` — the current
shared-page-with-role-checks approach works correctly, this is organizational, not a functional
gap), persistent doctor-unverified badge (currently only shown once at registration), SOS's
3-second cancel window + rapid-repeat rate limiting, and cleanup of unused mismatched-style
component files (`MedicationForm/Table`, `AppointmentForm/Table`, `VisitNoteForm/History`). Google
Calendar OAuth is wired in but unverified beyond "doesn't crash the app" — nobody has real Google
Cloud OAuth credentials to test the actual flow against.

---

# Phase 1 audit (original, 2026-08-20)

Date: 2026-08-20
Scope: compare current repo state against `README.md`'s target design (three roles, `care_links` connection model, shared `notifications` table, Modules 1–3).

Overall picture: the backend has real, mostly-working pieces for auth, vitals, AI report/symptom/diet features, notifications, and safety check-ins — but roughly a third of the built code is **dead** (routers that exist but are never registered in `main.py`), the **connections model is not the spec'd `care_links` many-to-many design**, **medications lost their patient linkage** in a migration, and there is **no working local setup** (no `.env.example`, seed script is broken, no setup docs). The frontend has no role-scoped routes and several components are almost certainly calling dead backend endpoints.

---

## Critical / blocks-the-app-from-running

| # | Issue | File(s) | Fix owner scope |
|---|---|---|---|
| 1 | No `.env.example` anywhere; `config.py` needs 10 env vars nobody documents | `backend/app/config.py` | shared/core |
| 2 | `seed_demo_data.py` references fields removed from the current `Medication`/`Appointment` models (`patient_id`, `schedule_time`, `scheduled_at`, `AppointmentStatus` import) — will `ImportError`/crash immediately, not just "runs but wrong" | `backend/seed_demo_data.py` | shared |
| 3 | `seed_demo_data.py` has no re-run guard — hardcoded emails will `IntegrityError` on a second run (violates team's own workflow rule) | same | shared |
| 4 | `requirements.txt` doesn't pin `alembic`, yet the project has migrations — fresh installs may not have alembic available | `backend/requirements.txt` | shared |
| 5 | Root `README.md` "Getting Started" is unmodified `create-next-app` boilerplate; no backend setup steps (venv, pip install, alembic upgrade, seed) documented at all | `README.md` | shared |

## Connections system (README §4) — not implemented as spec'd

| # | Issue | File(s) |
|---|---|---|
| 6 | Table is named `patient_links`, not `care_links`, and is missing fields the spec requires: `link_role`, `permission_level`, `status` (pending/active/revoked/declined), `invite_code`, `invited_by`, timestamps. Currently just `patient_id`, `viewer_id`, `relationship_label` — i.e. **no two-sided approval, no revoke, no invite flow at all** — every "connection" is presumably auto-active today. | `backend/app/models/user.py` |
| 7 | `patient_id`/`viewer_id` on `PatientLink` have no `ForeignKey` constraint (raw UUID columns) — referential integrity isn't enforced at the DB level, unlike every other linkage in the app | `backend/app/models/user.py` |

This is the single biggest structural gap versus the spec and needs a team decision (see "Needs a team decision" below) since `patient_links` is presumably owned by whoever built auth/dashboard.

## Dead code — built but unreachable (not wired into `main.py`)

| # | Router file | What it implements | Table it depends on |
|---|---|---|---|
| 8 | `app/routes.py` | old-style medication CRUD (conflicts in prefix with `routers/medications.py`) | `medications` (but wrong shape — see #12) |
| 9 | `app/appointments.py` | appointment CRUD | `appointments` |
| 10 | `app/medication_logs.py` | medicine adherence logs (README §8.4) | `medication_logs` — **table was never migrated** (commented out in the one alembic migration) |
| 11 | `app/visit_notes.py` | doctor visit notes/prescriptions (README §8.3) | `visit_notes` — **table was never migrated** (commented out in the one alembic migration) |
| 12 | `app/calendar.py` | Google Calendar OAuth + event sync (README §7.2) | fully built, just never imported |
| 13 | `routers/auth_stub.py` | duplicate of `routers/auth.py`, same `/auth` prefix | leftover from a merge, should be deleted |

Frontend components `AppointmentForm/Card/Table`, `MedicationForm/Card/Table`, `VisitHistory`, `VisitNoteForm` almost certainly call these dead endpoints today and are silently broken in the running app.

## Medications — broken data model

| # | Issue |
|---|---|
| 14 | `Medication` model has **no `patient_id`/owner column** post-migration — medications are effectively global/unscoped. `routers/medications.py` is registered but has zero endpoints (a placeholder comment). `routers/dashboard.py:63-68` hardcodes `_fetch_active_medications()` to `return []` with a comment admitting this. This breaks README §6.2/§8.4/§5 (medication tiles, adherence tracker) entirely. |

## Other broken/inconsistent endpoints

| # | Issue | File |
|---|---|---|
| 15 | `DELETE /contacts/{contact_id}` takes `contact_id: int` but `EmergencyContact.id` is a UUID — delete can never match a real row | `backend/app/routers/emergency.py:46` |
| 16 | `emergency.py` router prefix is `/api/emergency`, inconsistent with every other router (no `/api` prefix elsewhere) — likely a frontend mismatch | `backend/app/routers/emergency.py` |
| 17 | SOS endpoint (`POST /sos`) swallows Twilio failures with a bare `except Exception: pass` (no logging, no visible failure) and does **not** write to the shared `notifications` table — violates README §7.3's explicit corner-case requirements (delivery-failure visibility, family/doctor notification even if SMS fails) | `backend/app/routers/emergency.py:88-91` |
| 18 | `ai_summary.py` shares the `/reports` prefix with `reports.py` — not a hard collision but confusing route organization | `backend/app/routers/ai_summary.py` |

## Frontend gaps

| # | Issue |
|---|---|
| 19 | No role-scoped route trees (`/patient/...`, `/family/...`, `/doctor/...` per README §2) — everything lives under shared `/dashboard/[patientId]`, `/health/[patientId]`, `/notifications/[patientId]`. Role handling appears to be client-side/conditional rather than route-structured. Needs a decision on whether to restructure routes to match the spec's site map or keep the current shared-page approach and just fix what's broken inside it. |
| 20 | No dedicated pages for emergency contacts/SOS, appointments, fall logger, daily check-in, medicine reminder, doctor notes, connections management — only reusable components exist, several wired to dead backend routes (see dead code section). |

## Housekeeping

| # | Issue |
|---|---|
| 21 | `backend/requirements-temp.txt` is a stale duplicate missing `groq`/`pypdf`/`google-generativeai`/`twilio` — should be deleted to avoid a teammate installing from the wrong file. |
| 22 | Root `README.md` has a stray leftover line ("main") suggesting an unresolved/careless merge. |

---

## What's actually working today (don't touch beyond bug fixes)

- Auth: register/login exist and are wired (`routers/auth.py`), JWT + bcrypt in `auth.py`. (Not yet verified: email verification, password reset, refresh tokens, rate limiting — likely missing per README §3, needs closer look in Phase 2.)
- Vitals CRUD + history (`routers/vitals.py`) — real DB-backed.
- AI report analyzer, symptom checker, diet advisor — all in `routers/vitals.py`, real DB-backed, use Groq/Gemini.
- Notifications feed (`routers/notifications.py`) — real `notifications` table, matches README §9 shape well. This is good news: the hard architectural piece (shared notification table) already exists correctly; it just isn't fed by every module yet (SOS doesn't write to it — see #17).
- Safety check-in model/service exists (`safety_checkin.py`, `safety_checkin_service.py`).
- Weekly report + AI summary services exist and are wired.

---

## Proposed fix order (Phase 2, per README priority)

1. **Environment & boot**: write `.env.example`, fix `requirements.txt` (add alembic, delete `requirements-temp.txt`), fix `seed_demo_data.py` to match current schema + add re-run guard, rewrite README setup section. Get `alembic upgrade head` + `uvicorn` + `next dev` working clean from a fresh clone.
2. **Auth gaps**: verify/add email verification, password reset, refresh-token flow, rate limiting per README §3 (needs a closer read of `auth.py`/`routers/auth.py` than this pass did).
3. **Connections system**: decide fate of `patient_links` vs `care_links` (see decision needed below), then implement invite code + two-sided approval + revoke + permission levels.
4. **Notifications backbone**: wire SOS (and check other modules) to write into the existing `notifications` table consistently — the table itself is already right, just needs to be the single write path everywhere.
5. **Medications**: add `patient_id` back to the `Medication` model + migration, implement real endpoints in `routers/medications.py`, fix `dashboard.py`'s hardcoded empty list.
6. **Wire or delete dead routers**: for each of `routes.py`, `appointments.py`, `medication_logs.py`, `visit_notes.py`, `calendar.py`, `auth_stub.py` — either finish/register them (adding the missing `medication_logs`/`visit_notes` tables via a new migration) or delete them if superseded. This needs a decision (below) since these look like they belong to specific teammates.
7. Frontend: build out missing pages, connect them to real (now-fixed) endpoints, add role-scoped route guards.
8. Visual/interaction polish last.

## Needs a team decision before I proceed

- **`patient_links` → `care_links` migration**: this touches the connections model that other members' code (dashboard, notifications, medications ownership) all depend on. I can design and implement the new schema + migration, but want confirmation before renaming/restructuring a table other members' routers query directly.
- **Fate of the 6 dead/unwired routers** (`appointments.py`, `medication_logs.py`, `visit_notes.py`, `calendar.py`, `routes.py`, `auth_stub.py`): wire them in (finishing the missing migrations for `medication_logs`/`visit_notes`) or delete as abandoned duplicates? These look like individual members' unfinished work, not something to unilaterally discard.
- **Frontend route restructuring**: keep current shared `/dashboard/[patientId]` pattern with client-side role checks, or restructure to the spec's `/patient/*`, `/family/*`, `/doctor/*` site map? This is a larger frontend refactor and affects whoever owns routing/navigation.

I'll wait for direction on these three before making structural changes. Everything else in the fix order above (env setup, seed script, obvious bugs like the UUID/int mismatch, SOS notification write, medications patient_id) is safe to fix directly as I go.
