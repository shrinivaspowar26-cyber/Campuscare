# Campus Care — Progress

## Current Stage
Implementation complete & verified.

## Completed
- Project topic finalized.
- Student/Staff and Admin roles defined.
- Core issue workflow defined.
- AI Studio UI reference screenshots generated.
- Technology stack finalized (HTML, CSS, Vanilla JS, Python, Flask, SQLite).
- SQLite database schema finalized and migrated (`users`, `reports`, `report_history`, `feedback`, `categories`, `maintenance_teams`).
- Flask backend API fully implemented:
  - Session auth and role guard decorators (`@login_required`).
  - Authentication endpoints (`/api/login`, `/api/register`, `/api/auth/current-user`, `/logout`).
  - Report lifecycle endpoints (`POST /api/reports`, `GET /api/reports`, `GET /api/reports/<id>`, `GET /api/reports/by-ticket/<ticket_id>`).
  - Admin management endpoints (`PATCH /api/reports/<id>/status`, `PATCH /api/reports/<id>/assign`, `GET /api/reports/<id>/history`).
  - Feedback endpoints (`POST /api/feedback`, `GET /api/feedback`).
  - Profile endpoints (`GET /api/profile`, `PUT/PATCH /api/profile`).
  - Master data endpoints (`GET /api/categories`, `GET /api/maintenance-teams`).
- Image upload support (`/static/uploads/`).
- Frontend API client (`static/js/api.js`) migrated to real backend API endpoints.
- Page routes guarded with server-side authentication and role restrictions.
- Full end-to-end integration and workflow verification completed.
- Live Geotagged Site Photo verification:
  - SQLite database migration: `latitude`, `longitude`, `location_accuracy`, `photo_captured_at` columns added with re-run safety.
  - Strict backend validation for mandatory photo and GPS coordinates (-90 to 90 lat, -180 to 180 lng, non-negative accuracy, JPEG magic byte content check, 10MB size limit, server-side capture timestamp).
  - Secure photo serving endpoint (`/static/uploads/<filename>`) enforcing session authentication and ownership access controls.
  - Live camera stream capture (`getUserMedia`) and high-accuracy GPS capture (`getCurrentPosition`) with canvas burned-in geotag banner overlay in `report-problem.html`.
  - Geotag display and Google Maps navigation integration in `report-details.html` and `admin-issues.html` modal with table indicator badge.
  - Legacy report backward compatibility verified.
- Photo Upload Alternative & Source Tracking (Step 22):
  - SQLite database migration: added `photo_source` column (`camera` or `upload`).
  - Dual ingestion pipeline: Camera (JPEG with watermark) or Device Upload (JPEG or PNG via file picker).
  - Client-side and server-side magic byte inspection and location capture.
- Text-Quality Checks & Fake-Report Screening (Step 23):
  - Configuration constants added: `TITLE_MIN_CHARS = 10`, `TITLE_MAX_CHARS = 100`, `TITLE_MIN_WORDS = 2`, `MAX_WORD_LENGTH = 25`, `MAX_REPEAT_CHARS = 3`, `DESCRIPTION_MIN_CHARS = 20`.
  - SQLite database migration: added `text_flagged`, `text_flag_reason`, and `trust_level` columns with re-run safety.
  - Shared validation `check_text_quality(title, description)` in `app.py`:
    - Hard rejects (HTTP 400): character count limits, minimum word count, word length cap, repeated character limits, absence of letters, description length, identical title and description. Zero file or database artifacts created on reject.
    - Soft flags: flags suspicious vowel ratios (<0% or >80%) in words >= 5 letters, excessive repetition (>50%), or high proportion of suspicious words (>40%). Preserves genuine reports in English, transliterated Hindi/Marathi, and Devanagari script.
  - Frontend validation in `report-problem.html`: real-time character count counters, live feedback hints, and submit lock until text and location/photo pass.
  - Admin UI: "Suspicious text" badge in issues table and Manage modal with reason banner, plus Trust Level filter (`All`, `High Trust`, `Low Trust (Flagged)`).
- Category Loading & Auth Protection Fix (Step 24):
  - Fixed syntax error in `templates/report-problem.html` that aborted script evaluation and prevented categories from populating the form dropdown.
  - Added `@login_required()` route protection to `GET /api/categories` and `GET /api/maintenance-teams`, returning HTTP 401 for guests and 8 seeded categories for authenticated student and admin sessions.
  - Verified category submission and admin category filtering.
- Email Notifications & Delivery System (Step 25):
  - Created `.gitignore` and `.env.example` protecting SMTP credentials.
  - SQLite database migration: added `email_notifications INTEGER DEFAULT 1` to `users` and created `email_log` table with status constraints (`sent`, `failed`, `skipped`).
  - Implemented asynchronous mailer module (`mailer.py`) using Python standard library (`smtplib`, `email.message`, `threading`).
  - Added dynamic Dev Mode logging to terminal and `instance/email_dev.log` when SMTP settings are not provided.
  - Integrated 4 automated milestone notification events: Report Submitted, Maintenance Team Assigned, Status Updated (`In Progress`, `Resolved` with feedback call-to-action), and Report Rejected (with reason).
  - Added email notification preference toggle in user Profile (`templates/profile.html`).
  - Verified header injection sanitization, failure resilience (failed SMTP does not block API or DB operations), and zero emails on feedback or deletion.
- HOD Login Diagnosis & Role Authorization Audit (Step 26):
  - Completed audit of `templates/login.html`, `static/js/`, `app.py`, `database.py`, `create_admin.py`, and database rows.
  - Verified `PROJECT_CONTEXT.md` architecture defines exactly two roles: `Student / Staff` (`student`) and `Facilities Admin` (`admin`); HOD is not a system role and staff/HODs share the Student / Staff reporting portal.
  - Identified root cause of "This account does not have the selected role" for HOD logins: User #1 (`hod@gmail.com`) was created as an `admin`, but default login tab selection is `Student / Staff` (`role="student"`), triggering expected server-side mismatch; logging in under `Facilities Admin` succeeds. User #7 (`varadwakarekar@gmail.com`, Name: "HOD") is registered as `student` and succeeds under `Student / Staff`.
  - Confirmed `login.html` contains no extraneous HOD tab.
  - Verified server-enforced RBAC: client role selection never grants authority; database role strictly governs session permissions.
  - Verified `init_db()` idempotency and core workflows with automated regression tests.
- Prepare for Safe GitHub Push (Step 27):
  - Verified repository git status and initialized local git repository.
  - Created hardened `.gitignore` excluding SQLite databases (`*.db`, `*.sqlite`, `instance/`), user uploads (`static/uploads/*`), environment secrets (`.env`, `.env.*`), virtual environments (`venv/`, `__pycache__/`, `*.pyc`), logs, and IDE/OS files.
  - Created `static/uploads/.gitkeep` so the uploads directory is tracked without including user photos.
  - Implemented production secret-key guard in `app.py`: supports `CAMPUS_CARE_SECRET` and `SECRET_KEY`, raises clear `RuntimeError` in production if missing, and warns in dev mode.
  - Ensured `static/uploads/` is created on startup via `os.makedirs(UPLOAD_FOLDER, exist_ok=True)`.
  - Created `.env.example` with clean placeholder variables and instructions.
  - Created `requirements.txt` containing only actual project dependencies (`Flask>=3.0.0`, `Werkzeug>=3.0.0`).
  - Updated `README.md` with complete setup instructions (clone, venv, requirements, `.env`, `create_admin.py`, `app.py`).
  - Confirmed zero hardcoded secrets or personal test data in tracked files.
  - Simulated fresh clone in `/tmp`: confirmed fresh database initialization, uploads directory creation, student registration, and authentication pass cleanly.
  - Confirmed `git ls-files` strictly tracks 35 code, style, doc, and template files without databases, uploads, or `.env`.

## Current Stack
- HTML
- CSS
- Vanilla JavaScript
- Python
- Flask
- SQLite

## In Progress
- Deployment preparation.

## Pending
- Production secret keys and WSGI server setup.

## Known Issues
- None. All linear implementation plan steps verified.

## Next Task
Deployment preparation (production secret keys, WSGI server configuration, HTTPS setup).

## Update Rule
Update this file after each meaningful task. Record only completed and verified work. Do not mark planned features as completed.
