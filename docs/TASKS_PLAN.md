# Linear Implementation Plan: Campus Care

Complete transition from frontend-mock prototype to full-stack SQLite + Flask application.

---

## Task Checklist

### Step 1: Session & Auth Decorator ✅
- [x] Add `@login_required(role=None)` decorator in `app.py`.
- [x] Add `GET /api/auth/current-user` endpoint (returns active session user info or 401).
- [x] Add `_user_payload()` helper — consistent JSON shape across all auth endpoints.

### Step 2: Database Schema Refinement ✅
- [x] Added `image_url TEXT` column to `reports` table (migration-safe via `PRAGMA table_info` guard).
- [x] Added `categories` table + 8 seeded rows.
- [x] Added `maintenance_teams` table + 8 seeded rows.
- [x] Seeds use `INSERT OR IGNORE` — safe to re-run `init_db()` without duplicates.

### Step 3: Core Report API Endpoints ✅
- [x] Created `static/uploads/` directory for uploaded photos.
- [x] `GET /api/categories` — returns seeded category list from DB.
- [x] `GET /api/maintenance-teams` — returns seeded team list from DB.
- [x] `POST /api/reports` — creates report, generates ticket ID (`CC-YYYY-NNN`), handles optional image upload, seeds first history entry. Students only.
- [x] `GET /api/reports` — filtered list (category, status, priority, search). Students see own reports only; admins see all.
- [x] `GET /api/reports/<int:id>` — single report by DB id with full history + feedback.
- [x] `GET /api/reports/by-ticket/<ticket_id>` — lookup by human-readable ticket ID.

### Step 4: Admin Management & Audit History ✅
- [x] Implement `PATCH /api/reports/<int:id>/status` (validates allowed statuses, restricted to admin).
- [x] Implement `PATCH /api/reports/<int:id>/assign` (assigns team, transitions status to Assigned, restricted to admin).
- [x] Insert audit trail records into `report_history` on every status/assignment change with notes.
- [x] Implement `GET /api/reports/<int:id>/history` (students view own, admins view all).
- [x] Verified via automated test suite.

### Step 5: Feedback & Profile API ✅
- [x] `POST /api/feedback` — students only, validates report is Resolved/Closed, blocks duplicates, auto-closes report on submit, logs history.
- [x] `GET /api/feedback` — students see own; admins see all; optional `?reportId=` filter.
- [x] `GET /api/profile` — returns current session user's full profile.
- [x] `PUT/PATCH /api/profile` — updates name, phone, department, identifier; email/role immutable.
- [x] Verified via automated test suite.

### Step 6: Frontend API Client Migration ✅
- [x] Rewrote `static/js/api.js` — all methods now call real Flask endpoints via `fetch()`.
- [x] `mock-data.js` no longer referenced by any API method (can be removed in Step 7 cleanup).
- [x] Added internal `_fetch()` helper for consistent error handling across all calls.
- [x] `getAdminStats()` and `getStudentStats()` computed from live report + feedback data.
- [x] `switchPersona()` replaced with a graceful error stub (dev-only, not valid in real auth).
- [x] All 17 method signatures used by templates preserved — zero breaking changes.

### Step 7: Route Protection & Template Link Cleanup ✅
- [x] Replaced generic unprotected `for page in PAGES` loop with explicit decorated route functions.
- [x] `student-dashboard`, `report-problem`, `my-reports`, `feedback` → `@login_required(role="student")`.
- [x] `admin-dashboard`, `admin-issues` → `@login_required(role="admin")`.
- [x] `report-details`, `profile` → `@login_required()` (any authenticated role).
- [x] Guests redirected to `/login`; wrong-role users blocked with 302.
- [x] Template JS redirects and `href` links confirmed already clean (no `.html` suffixes).
- [x] Verified via automated tests covering guest, student, and admin access combinations.

### Step 8: End-to-End Verification ✅
- [x] Test student registration and login.
- [x] Submit report with image upload (stored in `/static/uploads/`).
- [x] Login as admin, view report in real-time, assign maintenance team, mark resolved.
- [x] Return to student session, verify status change and audit trail history.
- [x] Submit star rating feedback (5/5), verify automatic transition to Closed.
- [x] Updated `docs/PROGRESS.md` with final verified state.

### Step 9: Clean Login Page & Role Switching ✅
- [x] Removed "Quick Demo Accounts" chip box and mock autofill handlers from `templates/login.html`.
- [x] Removed dummy prefilled email/password attributes from input fields.
- [x] Role tabs ("Student / Staff" vs "Facilities Admin") switch cleanly, clearing inputs without injecting fake credentials.
- [x] Added informational note for admin role clarifying that admin accounts are managed by system administration (`python create_admin.py`).

### Step 10: Remove Demo Reset Controls ✅
- [x] Removed "Reset Demo Data" button (`#btn-reset-demo`) and listener from `static/js/components.js`.

### Step 11: Remove Evaluation Persona Switcher ✅
- [x] Removed "Evaluation Persona Switcher" card and quick-switch buttons from `templates/profile.html`.
- [x] Removed corresponding persona switch event listeners in `templates/profile.html`.

### Step 12: Final UI Cleanup Verification ✅
- [x] Tested student & admin login flows without demo artifacts.
- [x] Verified header component and profile pages render cleanly without broken references.
- [x] Verified all forms function properly without mock data interference.

### Step 13: Fix Admin Issue Manager 404 (ID Handling & Endpoints) ✅
- [x] Updated `app.py` status, assign, get, and history endpoints to accept both integer DB IDs and string ticket IDs (e.g. `CC-2026-108`).
- [x] Verified admin can assign team and update status using both ticket ID string and numeric DB ID without 404.

### Step 14: Implement "Delete / Remove Report" (API & UI) ✅
- [x] Added `DELETE /api/reports/<ticket_or_id>` in `app.py` (restricted to Admins, cascades deletion of history and feedback).
- [x] Added `CampusCareAPI.deleteReport(id)` in `static/js/api.js`.
- [x] Added "Remove Report" button with confirmation prompt in `templates/admin-issues.html` (Manage modal) and `templates/report-details.html` (for Admins).
- [x] Cleaned up automated test reports (1-7) from database; preserved Karan Sutar's report `CC-2026-108`.
- [x] Verified via test script: student deletion returns 403, admin deletion returns 200 and removes ticket cleanly.

### Step 15: Remove "Quick Persona Switch" from Sidebar & Fix Sidebar URLs ✅
- [x] Removed "Quick Persona Switch" section title, button (`#quick-toggle-role-btn`), and event listener from `static/js/components.js`.
- [x] Fixed all sidebar navigation paths to canonical Flask routes (`/student-dashboard`, `/report-problem`, `/my-reports`, `/admin-dashboard`, `/admin-issues`, `/feedback`, `/profile`, `/login`).
- [x] Fixed client-side auth guard check and redirection targets in `static/js/components.js`.

### Step 16: Fix Feedback Route Permissions & Show Latest 5 Reviews ✅
- [x] Updated route guard in `app.py` for `/feedback` and `/feedback.html` to `@login_required(role="admin")`.
- [x] Updated `api_get_feedback` in `app.py` to support `?limit=<int>` query parameter.
- [x] Updated `static/js/api.js` `getAllFeedback(limit)` to pass the limit.
- [x] Updated `templates/feedback.html` to query and display the latest 5 verified reviews.
- [x] Verified via test script: admin gets 200, student gets redirected, `?limit=5` respected.

### Step 17: End-to-End Verification of Admin Controls ✅
- [x] Verified admin can edit issue status and assign maintenance team without 404 errors using ticket IDs.
- [x] Verified admin can permanently delete reports using the new "Remove Report" button (with cascades).
- [x] Verified Feedback & Reviews page opens cleanly for admins with HTTP 200, showing up to the latest 5 verified reviews.
- [x] Verified sidebar contains no Persona Switch, no demo reset, and all links use canonical Flask routes.
- [x] Automated test suite passed with zero errors (`ALL_STEP_17_VERIFICATION_TESTS_PASSED_CLEANLY`).

### Step 18: Remove 4th Floor from Report Problem Form ✅
- [x] Removed `<option value="4th Floor">4th Floor & Above</option>` from `templates/report-problem.html`.

### Step 19: Fix Feedback Submission Endpoint (Support Ticket ID & DB ID) ✅
- [x] Updated `POST /api/feedback` in `app.py` to use `_find_report_row(conn, report_target)`.
- [x] Enabled submitting feedback via human-readable ticket ID string (e.g. `CC-2026-108`) as well as numeric DB ID.
- [x] Verified feedback links properly to report, transitions status to Closed, and records in audit history without "Report Not Found" errors.

### Step 20: Verification of Floor Form & Feedback Flow ✅
- [x] Verified floor dropdown in `templates/report-problem.html` contains no 4th floor option.
- [x] Verified student feedback submission on resolved ticket (`CC-2026-101`) succeeds with HTTP 201 without "Report Not Found" error.
- [x] Verified ticket automatically transitions to Closed, feedback is attached, and displays in the admin feedback ledger.
- [x] Automated test suite passed with zero errors (`ALL_STEP_20_VERIFICATION_TESTS_PASSED_SUCCESSFULLY`).

### Step 21: Mandatory Live Geotagged Site Photo for Every Report ✅
- [x] Database migration: Added `latitude REAL`, `longitude REAL`, `location_accuracy REAL`, `photo_captured_at TEXT` to `reports` table using `PRAGMA table_info` guard in `database.py`.
- [x] Backend validation in `app.py`:
  - Enforced mandatory live site photo and GPS coordinates (`latitude`, `longitude`, `location_accuracy`).
  - Validated numeric ranges: latitude (-90 to 90), longitude (-180 to 180), accuracy (non-negative).
  - Validated real JPEG magic bytes (`\xff\xd8`), empty file rejection, and 10MB size limit.
  - Generated secure server-side UUID filenames saved to `static/uploads/`.
  - Set server-side UTC ISO timestamp for `photo_captured_at`.
  - Secured photo route (`/static/uploads/<filename>`) with `@login_required()` and ownership check (students see only their own, admins see all).
- [x] Frontend report form in `templates/report-problem.html`:
  - Replaced file upload with live camera capture using `navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } })`.
  - Captured video frame onto `<canvas>` and burned GPS coordinates (lat, lng, accuracy) and timestamp banner into the JPEG blob.
  - Acquired live GPS coordinates at capture moment via `navigator.geolocation.getCurrentPosition({ enableHighAccuracy: true, maximumAge: 0 })`.
  - Handled permission denials, camera not found, location unavailable, timeout, and insecure context warnings.
  - Disabled submit button until valid photo and coordinates are captured.
  - Added retake functionality and auto-stop stream on capture or page unload.
- [x] UI display updates:
  - `templates/report-details.html`: Displays live site photo preview, coordinates, accuracy, captured timestamp, and "Open in Maps" link (`https://www.google.com/maps?q=<lat>,<lng>`). Shows "No location attached" for legacy reports.
  - `templates/admin-issues.html`: Displays photo preview, coordinates, accuracy, timestamp, and Maps link in Manage modal. Shows `📍 Geotagged` badge in master table.
- [x] Automated testing:
  - Verified `init_db()` migration safety when executed repeatedly.
  - Verified 400 errors for missing photo, missing coordinates, out-of-range coordinates, non-numeric values, non-JPEG files, and oversized files.
  - Verified report creation, persistence across restarts, and student/admin access controls.

### Step 22: Photo Upload as Alternative to Live Camera Capture ✅
- [x] Database migration: Added `photo_source TEXT` (`camera` or `upload`, nullable for legacy reports) with `PRAGMA table_info` guard.
- [x] Backend validation in `app.py`:
  - Required `photo_source` parameter (`camera` or `upload`).
  - Implemented binary magic-byte inspection: `\xff\xd8` for JPEG (camera and upload), `\x89PNG\r\n\x1a\n` for PNG (upload only).
  - Enforced 10MB size limit, UUID server-generated filenames, and return `photoSource` across endpoints.
- [x] Frontend report form in `templates/report-problem.html`:
  - Added tab switcher between "Take Photo" and "Upload Photo", cleanly stopping camera and clearing state when switching.
  - Added drag-and-drop / file picker for JPEG and PNG images.
  - Triggered immediate device GPS acquisition with informative note: "Location is your current device location, not read from the photo. Please submit from the issue site."
  - Added "Retry location" button and validation messages for invalid file type or oversized file.
- [x] Display & Verification:
  - Added source badges and notes in `report-details.html` and `admin-issues.html`.
  - Tested both camera and upload flows end-to-end.

### Step 23: Text-Quality Checks for Report Title and Description ✅
- [x] Configuration constants added to `app.py`:
  - `TITLE_MIN_CHARS = 10`, `TITLE_MAX_CHARS = 100`
  - `TITLE_MIN_WORDS = 2`
  - `MAX_WORD_LENGTH = 25`
  - `MAX_REPEAT_CHARS = 3`
  - `DESCRIPTION_MIN_CHARS = 20`
- [x] Database migration in `database.py`:
  - Added `text_flagged INTEGER DEFAULT 0`, `text_flag_reason TEXT`, and `trust_level TEXT DEFAULT 'high'` to `reports` table using `PRAGMA table_info` guard.
  - Verified `init_db()` is migration-safe and legacy rows load with default values.
- [x] Shared validation function `check_text_quality(title, description)` in `app.py`:
  - Hard reject (400): title length out of bounds, fewer than 2 words, word length > 25, character repeated > 3 times in a row, no letters (digits/symbols only), description < 20 chars, title and description identical.
  - Soft flags (accepted, `text_flagged = 1`, `trust_level = 'low'`): Latin words >= 5 letters with 0 vowels or > 80% vowels, same word making up > 50% of words, > 40% of words flagged. Excludes short words (<=4 chars), all-caps acronyms (AC, LAN, CCTV), words with digits, and non-Latin scripts (Devanagari).
- [x] Integration in `app.py`:
  - Invoked `check_text_quality` before photo processing and before DB insert so rejected submissions leave no orphaned files in `static/uploads/` and no database rows.
  - Updated `_report_row_to_dict` to return `textFlagged`, `textFlagReason`, and `trustLevel`.
  - Added `trust_level` filtering to `GET /api/reports`.
- [x] Frontend report form in `templates/report-problem.html`:
  - Added live character counters for title (`X/100`) and description (`X chars (min 20)`).
  - Added instant client-side validation mirroring hard-reject rules.
  - Submit button disabled until both valid text quality and valid photo + GPS coordinates are present.
  - Displays backend error messages on 400.
- [x] Admin UI visibility in `templates/admin-issues.html` and `templates/report-details.html`:
  - Added "⚠️ Suspicious text" badge in admin table rows and report details.
  - Added warning banner with flag reason in Manage modal and admin report details.
  - Added Trust Level filter (`All`, `High Trust`, `Low Trust (Flagged)`) to admin issues table.
- [x] Automated testing:
  - Verified `init_db()` idempotency across multiple runs.
  - Tested hard rejects (keyboard mash, repetition, digits only, short title, identical title/desc, 26-letter word) returning 400 with 0 files and 0 rows created.
  - Tested accepted genuine reports (English, Marathi/Hindi transliterated, Devanagari) passing with no flags (`trustLevel='high'`).
  - Tested soft flagged reports (unusual vowel ratios, repetitive words, gibberish description) accepted with `text_flagged=1` and `trustLevel='low'`.
  - Tested trust level filtering in `GET /api/reports`.

### Step 24: Fix Issue Categories Loading & Endpoint Protection ✅
- [x] Identified root cause: an extraneous closing brace `}` on line 565 of `templates/report-problem.html` broke script parsing (`SyntaxError: missing ) after argument list`), preventing `CampusCareAPI.getCategories()` from populating `#category-select`.
- [x] Removed syntax error from `templates/report-problem.html`.
- [x] Added `@login_required()` route guards to `GET /api/categories` and `GET /api/maintenance-teams` in `app.py` so unauthenticated guests are rejected with HTTP 401 while student and admin sessions receive the 8 categories.
- [x] Automated tests verified:
  - `init_db()` run twice: 8 seeded categories preserved with `INSERT OR IGNORE`.
  - `GET /api/categories` rejects guests (401) and returns 8 categories for student and admin (200).
  - Report problem form categories populate, submit, and persist category properly to SQLite.
  - Admin issue category filter returns and filters correctly.
  - Camera, upload, and text-quality screening remain intact.

### Step 25: Email Notifications for Report Updates ✅
- [x] Environment configuration & safety:
  - Created `.gitignore` ignoring `.env`, `*.log`, credentials, and temporary build files.
  - Created `.env.example` with template SMTP variables (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `MAIL_FROM`, `APP_BASE_URL`).
  - Implemented dynamic Dev Mode when SMTP variables are unset: prints formatted emails to console and logs to `instance/email_dev.log`.
- [x] Database migration in `database.py`:
  - Added `email_notifications INTEGER DEFAULT 1` to `users` table with `PRAGMA table_info` guard.
  - Created `email_log` table (`id`, `report_id`, `to_email`, `event`, `status`, `error`, `created_at`) with status constraint (`sent`, `failed`, `skipped`).
  - Verified `init_db()` runs cleanly and idempotently.
- [x] Background asynchronous email helper (`mailer.py`):
  - Standard library only (`smtplib`, `email.message`, `threading`).
  - Dispatches delivery in daemon background threads without blocking API responses.
  - Header injection prevention: strips `\r` and `\n` from subject lines.
  - Catches all SMTP/socket exceptions, ensuring API returns success and database commits persist even on connection failure.
  - Generates plain-text messages with direct links (`APP_BASE_URL/report-details?id=<ticket>`).
- [x] Event triggers integrated into `app.py`:
  - **Report Submitted**: Instant confirmation email with ticket ID and tracking link.
  - **Team Assigned**: Dispatch notice with team name and tracking link.
  - **Status Updated (`In Progress`, `Resolved`)**: Transition updates; includes feedback call-to-action for `Resolved`.
  - **Report Rejected**: Notice with administrative rejection reason and link.
  - Verified no emails sent on feedback submission or report deletion.
- [x] User preferences & UI:
  - Added Email Notifications checkbox to `templates/profile.html`.
  - Updated `_user_payload` and `api_update_profile` with server-side validation.
  - Skips delivery and records status `skipped` in `email_log` when notifications are disabled.
  - Added `Rejected` status option to admin triage filter and modal in `templates/admin-issues.html`.
  - Added `.status-badge.rejected` in `static/css/styles.css`.
- [x] Automated testing:
  - Verified `init_db()` idempotency across multiple runs.
  - Tested all 4 events in Dev Mode: verified console/log outputs and `email_log` records with `status='sent'`.
  - Tested wrong SMTP credentials: API returned 201/200, DB changes persisted, and `email_log` recorded `status='failed'` with error details.
  - Tested opt-out: `email_log` recorded `status='skipped'` with zero email delivery.
  - Tested header injection sanitization.
  - Tested ticket ID generation resilience (`MAX(id)` guard against collisions).
  - Tested zero emails on feedback and admin delete with clean FK cascades.### Step 26: HOD Role Login Diagnosis & System Role Audit ✅
- [x] Codebase & Schema Inspection:
  - Audited `templates/login.html`: Confirmed only two role tabs exist: "Student / Staff" (`data-role="student"`) and "Facilities Admin" (`data-role="admin"`). No HOD tab exists in the frontend UI.
  - Audited `app.py`: `/api/login` and `/login` compare database role (`user["role"]`) against requested role string (`student` or `admin`). Supported roles in session guards and decorators are exclusively `admin` and `student`.
  - Audited `database.py`: `users` schema strictly enforces `role TEXT NOT NULL CHECK(role IN ('student', 'admin'))`.
  - Audited `create_admin.py`: Provisions accounts with hardcoded `role = 'admin'`. Public registration `/api/register` provisions accounts with hardcoded `role = 'student'`. No script or API endpoint exists to create an `hod` role account.
  - Audited `instance/campus_care.db`:
    - User #1: email `hod@gmail.com`, name `hod`, role `'admin'` (created as admin via `create_admin.py`).
    - User #7: email `varadwakarekar@gmail.com`, name `HOD`, role `'student'` (created via public registration).
    - Zero rows have role `'hod'`.
- [x] Root Cause Analysis:
  - The project specification (`PROJECT_CONTEXT.md`) defines exactly two user roles: `Student / Staff` and `Admin`. "HOD" was never an application role.
  - When user logs in with email `hod@gmail.com`, the login form defaults to the `Student / Staff` tab (`role="student"`). Submitting without toggling to `Facilities Admin` causes a role mismatch against `user["role"]` (`admin`), returning HTTP 403: `"This account does not have the selected role."`.
  - Logging in with `hod@gmail.com` under `Facilities Admin` succeeds as an administrator.
  - Logging in with `varadwakarekar@gmail.com` (Name: "HOD") succeeds under `Student / Staff` as a student/staff reporter.
- [x] Verification:
  - Created automated test suite `scratch/test_hod_login_diagnostic.py`.
  - Verified `init_db()` idempotency (safe across repeated runs).
  - Verified role matching: valid tab succeeds (200), wrong tab returns HTTP 403 `"This account does not have the selected role."`, submitting `role="hod"` returns HTTP 403.
  - Verified route protections: guests redirected to `/login`, students blocked on admin routes, admins blocked on student routes.
  - Confirmed all existing flows (reporting, email notifications, categories, fake report screening) remain intact.

### Step 27: Prepare for Safe GitHub Push ✅
- [x] Git repository initialization:
  - Checked `git status`: directory was not previously a git repo; initialized clean local repository with `git init`.
- [x] `.gitignore` hardening:
  - Configured exclusions for SQLite databases (`*.db`, `*.sqlite`, `*.sqlite3`, `instance/`), user uploads (`static/uploads/*`, keeping `static/uploads/.gitkeep`), environment files (`.env`, `.env.*`), Python byte-code and virtual environments (`venv/`, `.venv/`, `__pycache__/`, `*.pyc`), log files (`*.log`), and OS/IDE metadata (`.DS_Store`, `.idea/`, `.vscode/`).
- [x] Secret scanning & environment variable guards:
  - Audited codebase for secrets, passwords, API keys, and personal credentials.
  - Updated `app.py`: supports `CAMPUS_CARE_SECRET` and `SECRET_KEY`; raises `RuntimeError` if missing in production (`FLASK_ENV=production`) and prints clear stderr warning in development.
  - Ensured `static/uploads/` is automatically created on startup via `os.makedirs(UPLOAD_FOLDER, exist_ok=True)`.
  - Sanitized `static/js/mock-data.js` dummy password fields and `README.md` placeholder strings.
- [x] Configuration & dependencies:
  - Created `.env.example` with placeholders for `CAMPUS_CARE_SECRET`, `PORT`, and SMTP options (no real credentials).
  - Created `requirements.txt` containing only actual project dependencies: `Flask>=3.0.0` and `Werkzeug>=3.0.0`.
- [x] Documentation & fresh-clone verification:
  - Updated `README.md` with complete, step-by-step setup instructions (git clone, venv, requirements, `.env`, `create_admin.py`, `app.py`).
  - Verified `git ls-files` strictly tracks only code and configuration files — zero databases, uploads, or `.env` files.
  - Tested fresh clone in `/tmp`: initialized database with 8 categories/teams, registered student, logged in, and verified uploads directory.

  - Verified role matching: valid tab succeeds (200), wrong tab returns HTTP 403 `"This account does not have the selected role."`, submitting `role="hod"` returns HTTP 403.
  - Verified route protections: guests redirected to `/login`, students blocked on admin routes, admins blocked on student routes.
  - Confirmed all existing flows (reporting, email notifications, categories, fake report screening) remain intact.
