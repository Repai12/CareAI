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

16. **AI Patient History Q&A** (Module 3) - doctor-only, matching README's role line verbatim
    ("Doctor ... uses AI to analyze reports, answers patient-history questions"). New
    `PatientQuestion` model/migration, `routers/patient_qa.py` (doctor + actively-managing-linked
    only, same permission bar as writing visit notes), and an `answer_patient_question()` helper
    grounding every answer in the patient's real latest vitals, active medications, recent visit
    notes, and recent symptom checks - not a generic response. Added a panel to the doctor's
    visit-notes page. Live testing caught two real bugs before they shipped: the new
    `PatientQaPanel` imported `StethoscopeIcon` from the wrong `icons.tsx` (the shared
    `components/icons.tsx` doesn't export it - that one only exists in the Health module's local
    icon file) which crashed the whole page with a blank screen, and the context-builder read
    `Medication.name`/`.dosage` when the real column is `medicine_name` - both would have been
    invisible without actually loading the page and asking a question, not just reading the code
    back. Fixed both, then verified the graceful-failure path end-to-end (keyless dev environment
    correctly returns "AI answer is temporarily unavailable" via 503, not a crash).

17. **Dual-Persona AI Companion** (Module 3) - patient-only. No detailed spec exists for what the
    two personas are, so picked two matching the product's own stated purpose (README overview:
    reduce isolation, keep patients safe without constant phone calls): "Companion" (warm, casual,
    targets loneliness) and "Coach" (upbeat, practical, nudges habits, lightly grounded in the
    patient's real recent vitals trend via the existing `_recent_vitals_context()` helper). New
    `CompanionMessage` model/migration, `routers/companion.py`, and a chat page with persona tabs
    at `/companion/[patientId]`, linked from the dashboard (patient-only). Each persona keeps its
    own separate thread so switching doesn't mix contexts. On a failed AI call, the user's message
    is deliberately NOT persisted (every saved user turn has a matching reply) and the frontend
    restores the draft text instead of losing it. Verified live: sent a message in the keyless dev
    environment, got the correct "temporarily unavailable" error with the draft preserved and the
    optimistic bubble rolled back cleanly; switching from Companion to Coach correctly loaded a
    separate (empty) thread rather than the same one.

18. **Family Chat over WebSockets** (Module 3, named explicitly in the Tech Stack table: "Real-time:
    WebSockets (family/doctor chat)") - the last of the five missing README features. New
    `ChatMessage` model/migration, `services/chat_manager.py` (a small in-memory per-patient
    connection registry - deliberately not a Redis pub/sub layer, this is a single-process
    dev/demo deployment, same scale assumption the rest of the project already makes), and
    `routers/chat.py`: a REST history endpoint plus `WS /ws/chat/{patient_id}`. The browser
    WebSocket API can't set an `Authorization` header, so the token travels as a query param and
    is verified with a new `decode_access_token()` helper factored out of `auth.py`'s existing
    `get_current_user` (one JWT-decode implementation either way). Access is patient-self or any
    actively-linked family/doctor, same bar as the dashboard. Frontend: `/chat/[patientId]` with a
    connection-status indicator, optimistic local send, and a one-shot reconnect-with-token-
    refresh on unexpected close (distinguishing a real access denial, code 4403, from "just
    reconnect"). Verified live with two real concurrent browser sessions (patient + linked family,
    two separate logins, not just two tabs sharing one) - a message sent from either side appeared
    in the other instantly with no page reload. That same two-tab test caught a real bug first:
    every message was rendering twice. Root cause was React Strict Mode's dev-only double-invoke
    of the connect effect racing ahead of the async history fetch - both invocations ended up
    opening their own live socket before either could be cancelled, so every broadcast arrived
    twice. Fixed by tracking a `cancelled` flag through the async chain and having `openSocket()`
    close any existing connection before opening a new one; re-tested and confirmed single
    delivery both directions. Deliberately not writing a `Notification` row per message (the
    whole point of the socket is realtime delivery; a notification-per-message would be noisy
    self-spam) - a documented scope line, not a missed corner case.


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

**Update (2026-08-20, later same day):** items 14-18 above closed the five README Features-table
entries that had zero code at all (mood tracking, AI prescription summarizer, AI patient history
Q&A, dual-persona AI companion, family chat over WebSockets) — see the scope note above item 14
for how that gap was found. Every README-listed feature now has real, live-verified code.

19. **Dead component cleanup** — deleted `MedicationForm/Table.tsx`, `AppointmentForm/Table.tsx`,
    `VisitNoteForm.tsx`, `VisitHistory.tsx`, and their entire supporting island
    (`services/api.ts`, `types/medication.ts`, `types/appointment.ts`, `types/visitNote.ts`) —
    10 files total. Confirmed via grep first that nothing under `app/` (the actual routed pages)
    imported any of them, directly or transitively; they were a fully self-contained, unreachable
    leftover from before the team rebuilt these features on the real backend. Verified live after
    deletion that Medications & Appointments and Visit Notes (the pages that share a name with the
    dead components) still load correctly.

20. **Persistent doctor-unverified badge + SOS safety hardening (README S13, corner cases)** —
    the doctor-unverified disclosure (README S13's known gap: a license number is required at
    signup but never checked against a real registry) was previously shown once, only on the
    registration success screen. Added a reusable `DoctorUnverifiedBadge` and wired it in
    everywhere a doctor's real account identity is shown to a patient/family viewer: the
    Connections page's pending/active doctor entries, each visit note's doctor byline, and the
    doctor's own dashboard header (a persistent self-reminder, not just a one-time notice).
    Deliberately left off free-text `Appointment.doctor_name` (that's a typed string, not
    necessarily a linked CareAI account, so the badge doesn't semantically apply there).

    Separately, replaced the SOS button's native `confirm()` dialog with an on-page 3-second
    countdown + Cancel button (same pattern real safety apps use — a brief, cancellable delay
    catches an accidental tap without adding real friction to a genuine emergency). Added a
    10-second rapid-repeat cooldown on the backend so an anxious user mashing the button doesn't
    fire a fresh SMS batch and notification-feed entry every time; a repeat within the window
    returns "already triggered Ns ago" instead. Live testing caught a real race condition in the
    first cooldown implementation: two near-simultaneous requests (a double-click, or in this
    case a stale-webpack-cache page crash that looped the request) could both read "no cooldown
    yet" before either had written its claim, letting both through - fixed with a `threading.Lock`
    that claims the cooldown slot *before* doing the actual SMS/notification work, not after, plus
    a try/except that releases the claim if the work itself fails. Re-verified: two genuinely
    spaced-apart triggers each created exactly one notification; a burst of requests within the
    same countdown collapsed to exactly one.

21. **Corner-case sweep across the 5 new features** — found and fixed four real gaps that a
    mechanical feature-by-feature build missed: (1) editing a visit note's `notes`/`prescription`
    didn't invalidate its cached `ai_summary`, so a doctor's edit could leave a stale AI
    explanation describing the old, now-wrong text — now cleared on any edit, regenerated on next
    request. (2) Mood tracking had no edit/delete, unlike the established Vitals pattern (a
    patient can already fix/remove a vitals entry) — added matching `PUT`/`DELETE
    /mood/{patient_id}/{mood_id}`, own-entry-only, plus a Delete button in the UI; verified live
    (logged an entry, deleted it, confirmed both the real `DELETE` network call and the empty
    state). (3)/(4) AI Companion messages and AI Patient History Q&A questions had no length cap
    (Family Chat already had one, 2000 chars) - added matching caps (2000 and 1000 chars) on both
    backend and frontend `maxLength` for consistency and to bound AI cost/abuse.

22. **Two more Module 3 gaps found on a second README cross-check** — re-reading the Features
    table line-by-line (not just section-by-section) turned up two more items that were
    incomplete or missing entirely, beyond the five built earlier today: "AI weekly health
    summaries" and "automated daily digest".
    - The existing Weekly Report was never actually AI-generated despite the name - it only ever
      built a raw HTML table dump. Added `summarize_weekly_report()` to `groq_health_service.py`
      (grounded in the week's real vitals/mood data, same graceful-None-on-no-key pattern as
      every other AI feature here) and wired it into `report_service.py` - the email now opens
      with a short AI narrative above the tables when Groq is available, and degrades to
      tables-only otherwise. Verified via direct call: report generation and the `EmailLog` audit
      trail both worked correctly with the narrative section cleanly absent (no key configured).
    - "Automated daily digest" didn't exist at all - no job, no notification category, nothing.
      Added `services/daily_digest_service.py`, a new `DIGEST` notification category, and a daily
      8 PM scheduler job (before the 9 PM missed-check-in job). Posts one Notification Center
      entry per patient summarizing the day (mood, latest vitals, active medication count,
      check-in status) - deliberately an in-app notification, not a second daily email on top of
      the weekly one, and deliberately skipped entirely for a patient with zero activity that day
      rather than posting a content-free "nothing happened" every single day. Added the missing
      "Daily Digest" filter tab to the Notification Center frontend. Verified live both ways: ran
      with no activity logged (correctly skipped, zero notifications), then logged a mood entry
      and re-ran (correctly created one notification with the right content, visible under both
      "All" and the new "Daily Digest" filter).

23. **Activity Tracking** (Module 1: "Activity tracking with trend dashboards") — a third README
    cross-check, this time re-reading Module 1 and 2 as carefully as Module 3, found this had
    zero code anywhere (confirmed by grep - not even a stray mention). No wearable integration
    exists in this app, so this is manual entry, same self-reported pattern as Mood/Vitals: patient
    logs an activity type (walk/exercise/chores/other) + duration + optional note, multiple
    entries/day allowed. New `ActivityLog` model/migration, `routers/activity.py` with edit/delete
    included from the start (unlike Mood, which needed a follow-up fix for this same gap - learned
    the lesson). "Trend dashboards" built as a 7-day daily-total-minutes bar chart using plain CSS
    (no charting library in this project, matching Mood's dot-trend approach), plus a new Activity
    tab in the Health module and an overview card. Verified live end-to-end as both patient
    (logged an entry, watched the bar chart update, deleted it via the real UI button) and family
    (confirmed read-only - no log form, history + chart only).

24. **Wellness Recommendation Engine** (Module 2: "wellness recommendation engine", listed as a
    separate item from "nutrition planner" in the same Module 2 line - the Diet Advisor already
    covers nutrition, this is the broader lifestyle counterpart). Zero code anywhere, confirmed
    by grep. New `WellnessRecommendation` model/migration, `routers/wellness.py`, and
    `generate_wellness_recommendations()` in `groq_health_service.py` - grounded in the patient's
    real recent vitals, mood, and activity trends (now that all three exist) rather than generic
    tips, same principle as the diet plan. New Wellness tab in the Health module, patient-only
    "Get wellness tips" / "Refresh recommendations" button, family/doctor read-only. Verified live:
    empty state renders correctly, generating in the keyless dev environment correctly surfaces a
    503 "temporarily unavailable" instead of crashing, and the nullable `GET .../latest` response
    (no recommendation generated yet) round-trips correctly through FastAPI's `X | None` response
    model.

25. **Medicine Reminder & Adherence Tracker: closed the "never actually automated" gap** — a
    corner-case check found that scheduling a reminder only ever created a `pending`
    `MedicationLog` row; nothing ever reminded the patient when it came due, and nothing ever
    transitioned an ignored reminder to `missed`. That meant the tracker's own "3 consecutive
    misses triggers a notification" logic (built in phase 6) could **never fire on its own** - it
    required a human to manually click "Missed" on every single overdue dose first, which defeats
    the point of an *automated* adherence tracker entirely. Added a new scheduler job (every 15
    minutes, not once-daily like the other jobs - a reminder is time-of-day specific) that: fires
    one in-app "time to take X" notification per dose the moment it's due (guarded by a new
    `reminder_sent_at` column so it never re-notifies the same dose), and auto-marks a dose
    `missed` if it's still `pending` 2 hours after its scheduled time, which then correctly feeds
    the existing streak check. Factored the streak-check helper out of `medication_logs.py`
    (dropped its leading underscore - it's now genuinely cross-module) rather than duplicating the
    query. Verified live via direct script calls: due-now reminder fires once and is idempotent on
    a second run, an overdue dose auto-transitions to `missed`, and three such misses in a row
    correctly fire the "3 consecutive misses" notification fully automatically for the first time.

**Not yet done**: frontend route restructuring (`/patient/*`, `/family/*`, `/doctor/*` — the current
shared-page-with-role-checks approach works correctly, this is organizational, not a functional
gap). Google Calendar OAuth is wired in but unverified beyond "doesn't crash the app" — nobody has real Google
Cloud OAuth credentials to test the actual flow against. Family Chat's connection registry is
in-memory/single-process by design (documented in `chat_manager.py`) — fine for this project's
scale, would need a shared pub/sub layer if it ever ran behind multiple workers.

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
