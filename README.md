# Campus Care

Campus facility problem reporting and maintenance tracking system. Students and staff report infrastructure issues; facilities administrators triage reports, dispatch maintenance crews, track resolution progress, and monitor student feedback.

## Tech Stack
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Backend**: Python 3, Flask
- **Database**: SQLite3 (`instance/campus_care.db`)

---

> [!IMPORTANT]
> **Browser Security Requirement for Camera & GPS Location:**
> The live camera (`navigator.mediaDevices.getUserMedia`) and GPS geolocation (`navigator.geolocation.getCurrentPosition`) APIs are browser security-sensitive features that strictly require a **Secure Context**. They will only operate over **HTTPS** or on **`localhost`** (`127.0.0.1`). Accessing the application over unencrypted plain HTTP on remote IP addresses will cause the browser to block camera and location permissions.

---

## Getting Started

### 1. Clone the Repository
```bash
git clone <repository-url>
cd care_campus
```

### 2. Create and Activate Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy the example environment template to `.env`:
```bash
cp .env.example .env
```
*(Optional)* Edit `.env` to configure a production `CAMPUS_CARE_SECRET` and SMTP credentials for live emails. If SMTP settings are omitted, the app runs in **Dev Mode** (emails print to console and log to `instance/email_dev.log`).

### 5. Initialize Database & Seed Master Data
The database tables and master categories are seeded automatically when running `app.py`, or you can initialize manually:
```bash
python3 database.py
```

### 6. Create Administrator Account
Admin accounts cannot be registered via public web registration; provision one securely via CLI:
```bash
python3 create_admin.py
```

### 7. Run Application
```bash
python3 app.py
```
Open your browser at `http://127.0.0.1:5001` (or `http://localhost:5001`).

---

## Features
- **Student / Staff Portal**: Register, log in, submit live geotagged problem reports, track 5-stage repair milestone progress, and provide 1–5 star resolution feedback.
- **Live Geotagged Site Photo & Upload**: Mandatory site photo (live camera capture with burned-in geotag watermark or device upload) with real-time GPS coordinates and Google Maps lookup.
- **Facilities Administration**: Overview dashboard with category statistics, master triage queue, maintenance team dispatching, status progression, and report deletion.
- **Strict Role-Based Access Control (RBAC)**: Scoped access for students (own reports only) and facilities administrators (global access), with secure photo serving routes.
- **Text-Quality & Fake-Report Screening**: Automated screening rejecting gibberish or spam submissions and flagging suspicious reports for administrative review.

---

## Text-Quality & Fake-Report Screening Rules

The system validates report titles and descriptions prior to saving uploaded files or persisting records to SQLite.

### Configuration Constants (`app.py`)
- `TITLE_MIN_CHARS = 10`: Minimum title length in characters.
- `TITLE_MAX_CHARS = 100`: Maximum title length in characters.
- `TITLE_MIN_WORDS = 2`: Minimum word count for titles (rejects titles without spaces).
- `MAX_WORD_LENGTH = 25`: Maximum permissible length for any individual word.
- `MAX_REPEAT_CHARS = 3`: Maximum consecutive repetitions of any character (e.g., `aaaa` is blocked).
- `DESCRIPTION_MIN_CHARS = 20`: Minimum description length in characters.

### Hard Reject Rules (HTTP 400)
Submissions matching any of these criteria are immediately rejected. No image is saved to `static/uploads/` and no database record is created:
1. Title shorter than 10 or longer than 100 characters.
2. Title with fewer than 2 words.
3. Any word in the title or description longer than 25 characters.
4. Any character repeated more than 3 times in a row (e.g. `aaaa`, `bbbbb`).
5. Title containing no letters (digits or symbols only).
6. Description shorter than 20 characters.
7. Title and description identical.

### Soft Flag Rules (`text_flagged = 1`, `trust_level = 'low'`)
Genuine-looking reports are accepted and stored, but marked as suspicious for admin inspection:
1. Latin words of 5+ letters with zero vowels (e.g. `qwrty`, `zxcvb`) or over 80% vowels.
2. The same word making up more than 50% of the text (e.g. `light light light light`).
3. More than 40% of words flagged by unusual vowel ratios.
*Exceptions*: Words of 4 characters or fewer, all-uppercase acronyms (e.g., `AC`, `LAN`, `CCTV`), words containing digits, and non-Latin scripts (e.g., Devanagari) are never flagged.

Flagged reports display a `⚠️ Suspicious text` badge in the admin triage table and a descriptive explanation in the Manage modal. Admins can filter the queue by Trust Level (`High Trust` vs. `Low Trust`).

---

## Email Notifications & SMTP Setup

Campus Care sends automated plain-text email notifications to report owners when key milestone events occur on their problem reports. Delivery runs asynchronously in background threads (`threading.Thread`) and will never block or delay user requests.

### Supported Events
1. **Report Submitted**: Instant confirmation with ticket ID, report title, and tracking link.
2. **Team Assigned**: Notification with ticket ID, assigned maintenance crew name, and tracking link.
3. **Status Updated (`In Progress`, `Resolved`)**: Progress updates. For `Resolved` issues, the email prompts the reporter to submit a 1–5 star rating and feedback.
4. **Report Rejected**: Notification with ticket ID, report title, and the administrative rejection reason.

### User Notification Preferences & Audit Log
- Users can toggle email notifications on or off in their **Profile** (`templates/profile.html`).
- If notifications are disabled (`email_notifications = 0`), no email is dispatched, and the action is logged with status `skipped`.
- Every dispatch attempt is recorded in the `email_log` SQLite table (`id`, `report_id`, `to_email`, `event`, `status`, `error`, `created_at`) with status `sent`, `failed`, or `skipped`. Sensitive information (passwords, email bodies) is never stored in the database.

### Dev Mode (Default)
If SMTP settings are not provided in the environment, Campus Care runs automatically in **Dev Mode**:
- Emails are **not sent over the network**.
- Formatted email contents (`To`, `From`, `Subject`, `Body`) are printed directly to the server terminal console.
- Copies are appended to `instance/email_dev.log`.
- Database logs record status `sent`.

### Environment Variables
Configure the following in a `.env` file (see `.env.example`):

| Variable | Description | Default / Example |
| :--- | :--- | :--- |
| `SMTP_HOST` | Outgoing SMTP server hostname | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port (STARTTLS) | `587` |
| `SMTP_USER` | SMTP username / account email | `user@example.com` |
| `SMTP_PASSWORD`| SMTP account password or app password | `xxxx xxxx xxxx xxxx` |
| `MAIL_FROM` | Sender email address | `no-reply@campuscare.local` |
| `APP_BASE_URL` | Base web application URL | `http://127.0.0.1:5001` |

### Testing with a Gmail App Password
To test live email delivery with a personal or Google Workspace Gmail account:
1. Log into your Google Account and navigate to **Security** $\rightarrow$ **2-Step Verification**.
2. Scroll to the bottom and select **App passwords** (2-Step Verification must be enabled).
3. Name the password (e.g., `Campus Care Dev`) and copy the generated 16-character code (e.g., `abcd efgh ijkl mnop`).
4. Set the environment variables in your terminal or `.env`:
   ```bash
   export SMTP_HOST=smtp.gmail.com
   export SMTP_PORT=587
   export SMTP_USER="your.email@gmail.com"
   export SMTP_PASSWORD="your-16-char-app-password"
   export MAIL_FROM="your.email@gmail.com"
   export APP_BASE_URL="http://127.0.0.1:5001"
   ```
5. Run the application (`python app.py`). Notifications will now deliver directly to report owners' inboxes.


