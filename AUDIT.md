# CareAI Audit

## Progress log (2026-08-20)

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

**Not yet done** — still open per the fix order below: a feature-by-feature real-user pass across the
AI features (symptom checker, diet advisor, report analyzer — currently believed working but not yet
re-verified against corner cases the way everything else has been), frontend route restructuring
(`/patient/*`, `/family/*`, `/doctor/*`), visual/interaction polish. Google Calendar OAuth is wired in
but unverified beyond "doesn't crash the app" — nobody has real Google Cloud OAuth credentials to test
the actual flow against.

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
