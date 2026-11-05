import os
import re
import sys
import uuid
import math
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify, send_from_directory
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from database import init_db, get_db
from mailer import (
    notify_report_submitted,
    notify_team_assigned,
    notify_status_changed,
    notify_report_rejected,
)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB maximum photo size

# Text Quality & Fake-Report Check Constants
TITLE_MIN_CHARS = 10
TITLE_MAX_CHARS = 100
TITLE_MIN_WORDS = 2
MAX_WORD_LENGTH = 25
MAX_REPEAT_CHARS = 3  # the same character may not repeat more than this many times in a row
DESCRIPTION_MIN_CHARS = 20


def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _is_jpeg(file_storage):
    """Validate that the uploaded file contains real JPEG magic bytes (FF D8)."""
    pos = file_storage.tell()
    file_storage.seek(0)
    header = file_storage.read(2)
    file_storage.seek(pos)
    return header == b"\xff\xd8"


def _detect_image_type(file_storage):
    """Detect image format by binary magic bytes. Returns 'jpg', 'png', or None."""
    pos = file_storage.tell()
    file_storage.seek(0)
    header = file_storage.read(8)
    file_storage.seek(pos)
    if header.startswith(b"\xff\xd8"):
        return "jpg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    return None


def _is_suspicious_word(word):
    """Check if a Latin-letter word is suspicious.

    Applies to Latin-letter words only. Skip for Devanagari and other scripts.
    Flags:
    - 5 or more letters with no vowels (a, e, i, o, u), OR vowels > 80% of letters.
    Excludes:
    - Words of 4 letters or fewer.
    - All-uppercase words (acronyms like AC, LAN, CCTV).
    - Words containing digits.
    """
    clean = re.sub(r"^[^\w]+|[^\w]+$", "", word)
    if not clean:
        return False

    # Do not flag words containing digits
    if any(c.isdigit() for c in clean):
        return False

    # Do not flag words of 4 letters or fewer
    if len(clean) <= 4:
        return False

    # Do not flag all-uppercase words (acronyms like AC, LAN, CCTV)
    if clean.isupper():
        return False

    # Check if purely Latin alphabet (skip Devanagari and other scripts)
    if not all(("a" <= c.lower() <= "z") for c in clean):
        return False

    vowels = sum(1 for c in clean.lower() if c in "aeiou")
    total = len(clean)

    if vowels == 0:
        return True
    if (vowels / total) > 0.80:
        return True

    return False


def check_text_quality(title, description):
    """Validate report title and description for text quality and suspicious patterns.

    Returns:
        (hard_error_message_or_None, soft_flags_list)
    """
    # Normalize first: strip, and collapse repeated whitespace
    title_norm = re.sub(r"\s+", " ", (title or "").strip())
    desc_norm = re.sub(r"\s+", " ", (description or "").strip())

    # --- HARD REJECT CHECKS (return 400 with clear message) ---
    if len(title_norm) < TITLE_MIN_CHARS:
        return (f"Title must be at least {TITLE_MIN_CHARS} characters.", [])

    if len(title_norm) > TITLE_MAX_CHARS:
        return (f"Title cannot exceed {TITLE_MAX_CHARS} characters.", [])

    title_words = title_norm.split()
    if len(title_words) < TITLE_MIN_WORDS:
        return (f"Title must contain at least {TITLE_MIN_WORDS} words (separated by spaces).", [])

    if len(desc_norm) < DESCRIPTION_MIN_CHARS:
        return (f"Description must be at least {DESCRIPTION_MIN_CHARS} characters.", [])

    if title_norm.lower() == desc_norm.lower():
        return ("Title and description cannot be identical.", [])

    # Title must have letters (cannot be only numbers or symbols)
    if not any(c.isalpha() for c in title_norm):
        return ("Title must contain letters (cannot be only numbers or symbols).", [])

    desc_words = desc_norm.split()
    for w in title_words + desc_words:
        if len(w) > MAX_WORD_LENGTH:
            return (f"Words cannot exceed {MAX_WORD_LENGTH} characters in length.", [])

    # The same character may not repeat more than MAX_REPEAT_CHARS times in a row
    repeat_pattern = re.compile(r"(.)\1{" + str(MAX_REPEAT_CHARS) + r",}")
    if repeat_pattern.search(title_norm) or repeat_pattern.search(desc_norm):
        return (f"Characters cannot repeat more than {MAX_REPEAT_CHARS} times in a row.", [])

    # --- SOFT FLAGS (flagged suspicious, lowered to low trust) ---
    soft_flags = []

    # 1. Repetitive word check (> 50% of words in title or description)
    def check_repetitive(words, context_name):
        if not words:
            return None
        cleaned_words = [re.sub(r"^[^\w]+|[^\w]+$", "", w).lower() for w in words]
        cleaned_words = [w for w in cleaned_words if w]
        if not cleaned_words:
            return None
        counts = {}
        for w in cleaned_words:
            counts[w] = counts.get(w, 0) + 1
        for w, cnt in counts.items():
            if cnt > (len(cleaned_words) / 2):
                return f"Repetitive word '{w}' makes up more than 50% of words in {context_name}."
        return None

    rep_title = check_repetitive(title_words, "title")
    if rep_title:
        soft_flags.append(rep_title)

    rep_desc = check_repetitive(desc_words, "description")
    if rep_desc:
        soft_flags.append(rep_desc)

    # 2. Vowel-ratio / suspicious words check (> 40% of words flagged)
    def check_suspicious_ratio(words, context_name):
        if not words:
            return None
        suspicious_count = sum(1 for w in words if _is_suspicious_word(w))
        if len(words) > 0 and (suspicious_count / len(words)) > 0.40:
            return f"Over 40% of words in {context_name} look suspicious (unusual vowel ratios or missing vowels)."
        return None

    sus_title = check_suspicious_ratio(title_words, "title")
    if sus_title:
        soft_flags.append(sus_title)

    sus_desc = check_suspicious_ratio(desc_words, "description")
    if sus_desc:
        soft_flags.append(sus_desc)

    return (None, soft_flags)

app = Flask(__name__)

# Security: Load secret key from environment (CAMPUS_CARE_SECRET or SECRET_KEY)
_raw_secret = os.environ.get("CAMPUS_CARE_SECRET") or os.environ.get("SECRET_KEY")
_is_prod = (
    os.environ.get("FLASK_ENV") == "production"
    or os.environ.get("ENV") == "production"
    or os.environ.get("NODE_ENV") == "production"
)

if not _raw_secret:
    if _is_prod:
        raise RuntimeError(
            "CRITICAL SECURITY CONFIGURATION ERROR: CAMPUS_CARE_SECRET (or SECRET_KEY) "
            "must be configured in production! Generate a secure secret key with: "
            "python -c 'import secrets; print(secrets.token_hex(32))' and set it in your environment."
        )
    print(
        "[WARNING] CAMPUS_CARE_SECRET / SECRET_KEY is not set in environment. "
        "Using a temporary local development key. Set CAMPUS_CARE_SECRET in your .env before deploying.",
        file=sys.stderr,
    )
    _raw_secret = "dev-insecure-key-do-not-use-in-production"

app.secret_key = _raw_secret

# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def login_required(role=None):
    """Decorator that enforces an active session, optionally checking role.

    Usage:
        @login_required()                  # any authenticated user
        @login_required(role="admin")      # admins only
        @login_required(role="student")    # students only
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            user_id = session.get("user_id")
            if not user_id:
                # API routes → JSON 401
                if request.path.startswith("/api/"):
                    return jsonify({"error": "Authentication required."}), 401
                # Page routes → redirect to login
                return redirect(url_for("login"))

            if role and session.get("role") != role:
                if request.path.startswith("/api/"):
                    return jsonify({"error": "Access denied."}), 403
                flash("You do not have permission to access that page.", "error")
                return redirect(url_for("login"))

            return f(*args, **kwargs)
        return wrapped
    return decorator


def _user_payload(user):
    """Return a JSON-serialisable dict for a db Row object."""
    return {
        "id":         user["id"],
        "name":       user["name"],
        "email":      user["email"],
        "role":       user["role"],
        "identifier": user["identifier"],
        "department": user["department"],
        "phone":      user["phone"],
        "emailNotifications": bool(user["email_notifications"]) if "email_notifications" in user.keys() and user["email_notifications"] is not None else True,
        "roleLabel":  "Facilities Administrator" if user["role"] == "admin" else "Student / Staff",
    }


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
@app.route("/register.html", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        identifier = request.form.get("identifier", "").strip()
        department = request.form.get("department", "").strip()
        phone = request.form.get("phone", "").strip()

        if not name or not email or len(password) < 8:
            flash("Enter your name and email, and use a password of at least 8 characters.", "error")
            return redirect(url_for("register"))

        try:
            with get_db() as conn:
                conn.execute("""
                    INSERT INTO users
                    (name, email, password_hash, role, identifier, department, phone)
                    VALUES (?, ?, ?, 'student', ?, ?, ?)
                """, (
                    name, email, generate_password_hash(password),
                    identifier, department, phone
                ))
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                flash("That email is already registered.", "error")
                return redirect(url_for("register"))
            raise

        flash("Account created. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
@app.route("/login.html", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        requested_role = request.form.get("role", "student")

        with get_db() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE email = ?", (email,)
            ).fetchone()

        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.", "error")
            return redirect(url_for("login"))

        if user["role"] != requested_role:
            flash("This account does not have the selected role.", "error")
            return redirect(url_for("login"))

        session.clear()
        session["user_id"] = user["id"]
        session["role"] = user["role"]

        destination = "admin_dashboard" if user["role"] == "admin" else "student_dashboard"
        return redirect(url_for(destination))

    return render_template("login.html")

# ---------------------------------------------------------------------------
# Auth API endpoints
# ---------------------------------------------------------------------------

@app.route("/api/auth/current-user")
@login_required()
def api_current_user():
    """Return the currently logged-in user's profile from the database."""
    with get_db() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE id = ?", (session["user_id"],)
        ).fetchone()

    if not user:
        # Session references a deleted user — clear and reject
        session.clear()
        return jsonify({"error": "User not found."}), 404

    return jsonify(_user_payload(user))


@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role_type = data.get("roleType", "student")
    identifier = data.get("identifier", "").strip()
    department = data.get("department", "").strip()
    phone = data.get("phone", "").strip()

    if not all([name, email, password, identifier, department, phone]):
        return jsonify({"error": "Please complete all required fields."}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must contain at least 6 characters."}), 400

    try:
        with get_db() as conn:
            cursor = conn.execute("""
                INSERT INTO users
                (name, email, password_hash, role, identifier, department, phone)
                VALUES (?, ?, ?, 'student', ?, ?, ?)
            """, (
                name, email, generate_password_hash(password),
                identifier, department, phone
            ))
            user_id = cursor.lastrowid

    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            return jsonify({"error": "That email is already registered."}), 409
        raise
    
    session.clear()
    session["user_id"] = user_id
    session["role"] = "student"

    # Fetch full row so _user_payload can populate all fields
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    return jsonify(_user_payload(user)), 201

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password") or ""
    role = data.get("role", "student")

    with get_db() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password."}), 401

    if user["role"] != role:
        return jsonify({"error": "This account does not have the selected role."}), 403

    session.clear()
    session["user_id"] = user["id"]
    session["role"] = user["role"]

    return jsonify(_user_payload(user))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# ---------------------------------------------------------------------------
# Reference data API
# ---------------------------------------------------------------------------

@app.route("/api/categories")
@login_required()
def api_categories():
    with get_db() as conn:
        rows = conn.execute("SELECT name FROM categories ORDER BY name").fetchall()
    return jsonify([r["name"] for r in rows])


@app.route("/api/maintenance-teams")
@login_required()
def api_maintenance_teams():
    with get_db() as conn:
        rows = conn.execute("SELECT name FROM maintenance_teams ORDER BY name").fetchall()
    return jsonify([r["name"] for r in rows])


# ---------------------------------------------------------------------------
# Reports API
# ---------------------------------------------------------------------------

def _report_row_to_dict(row, conn):
    """Convert a reports DB row to the JSON shape the frontend expects."""
    # Fetch reporter info
    reporter = conn.execute(
        "SELECT id, name, email, role FROM users WHERE id = ?", (row["user_id"],)
    ).fetchone()

    # Fetch audit history
    history_rows = conn.execute(
        """SELECT action, note, created_at, user_id
           FROM report_history
           WHERE report_id = ?
           ORDER BY created_at ASC""",
        (row["id"],),
    ).fetchall()

    history = []
    for h in history_rows:
        actor = None
        if h["user_id"]:
            actor = conn.execute(
                "SELECT name, role FROM users WHERE id = ?", (h["user_id"],)
            ).fetchone()
        history.append({
            "timestamp": h["created_at"],
            "status":    h["action"],
            "note":      h["note"] or "",
            "updatedBy": f"{actor['name']} ({'Admin' if actor['role'] == 'admin' else 'Student'})" if actor else "System",
        })

    # Fetch feedback if any
    fb = conn.execute(
        "SELECT rating, comments, created_at FROM feedback WHERE report_id = ?",
        (row["id"],),
    ).fetchone()

    keys = row.keys()
    return {
        "id":           row["ticket_id"],
        "dbId":         row["id"],
        "title":        row["title"],
        "category":     row["category"],
        "location": {
            "building": row["building"],
            "floor":    row["floor"] or "",
            "roomArea": row["room"] or "",
        },
        "priority":         row["priority"],
        "status":           row["status"],
        "assignedTeam":     row["assigned_team"],
        "imageUrl":         row["image_url"],
        "latitude":         row["latitude"] if "latitude" in keys else None,
        "longitude":        row["longitude"] if "longitude" in keys else None,
        "locationAccuracy": row["location_accuracy"] if "location_accuracy" in keys else None,
        "photoCapturedAt":  row["photo_captured_at"] if "photo_captured_at" in keys else None,
        "photoSource":      row["photo_source"] if "photo_source" in keys else None,
        "textFlagged":      bool(row["text_flagged"]) if "text_flagged" in keys and row["text_flagged"] is not None else False,
        "textFlagReason":   row["text_flag_reason"] if "text_flag_reason" in keys else None,
        "trustLevel":       row["trust_level"] if "trust_level" in keys and row["trust_level"] else ("low" if ("text_flagged" in keys and row["text_flagged"]) else "high"),
        "reportedBy": {
            "id":    reporter["id"],
            "name":  reporter["name"],
            "email": reporter["email"],
        } if reporter else None,
        "createdAt":  row["created_at"],
        "updatedAt":  row["updated_at"],
        "description": row["description"],
        "history":    history,
        "feedback":   {
            "rating":    fb["rating"],
            "comments":  fb["comments"],
            "createdAt": fb["created_at"],
        } if fb else None,
    }


@app.route("/api/reports", methods=["GET"])
@login_required()
def api_get_reports():
    """Return reports list. Students see only their own; admins see all."""
    user_id = session["user_id"]
    role    = session["role"]

    category = request.args.get("category", "").strip()
    status   = request.args.get("status",   "").strip()
    priority = request.args.get("priority", "").strip()
    trust_level = (request.args.get("trust_level") or request.args.get("trustLevel") or "").strip().lower()
    search   = request.args.get("search",   "").strip().lower()

    query  = "SELECT * FROM reports WHERE 1=1"
    params = []

    # Students can only see their own reports
    if role == "student":
        query += " AND user_id = ?"
        params.append(user_id)

    if category and category != "All":
        query += " AND category = ?"
        params.append(category)

    if status and status != "All":
        query += " AND status = ?"
        params.append(status)

    if priority and priority != "All":
        query += " AND priority = ?"
        params.append(priority)

    if trust_level and trust_level != "all":
        query += " AND LOWER(trust_level) = ?"
        params.append(trust_level)

    query += " ORDER BY created_at DESC"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        reports = [_report_row_to_dict(r, conn) for r in rows]

    # Apply search filter in Python (covers ticket_id, title, description, location)
    if search:
        reports = [
            r for r in reports
            if search in (r["id"] or "").lower()
            or search in (r["title"] or "").lower()
            or search in (r["description"] or "").lower()
            or search in (r["location"]["building"] or "").lower()
            or search in (r["location"]["roomArea"] or "").lower()
        ]

    return jsonify(reports)


def _find_report_row(conn, ticket_or_id):
    """Find a report row by integer id or string ticket_id."""
    if isinstance(ticket_or_id, int) or (isinstance(ticket_or_id, str) and ticket_or_id.isdigit()):
        row = conn.execute("SELECT * FROM reports WHERE id = ?", (int(ticket_or_id),)).fetchone()
        if row:
            return row
    return conn.execute("SELECT * FROM reports WHERE ticket_id = ?", (str(ticket_or_id),)).fetchone()


@app.route("/api/reports/<int:report_db_id>", methods=["GET"])
@app.route("/api/reports/<ticket_id>", methods=["GET"])
@login_required()
def api_get_report(report_db_id=None, ticket_id=None):
    target = report_db_id if report_db_id is not None else ticket_id
    with get_db() as conn:
        row = _find_report_row(conn, target)

        if not row:
            return jsonify({"error": "Report not found."}), 404

        # Students may only view their own reports
        if session["role"] == "student" and row["user_id"] != session["user_id"]:
            return jsonify({"error": "Access denied."}), 403

        return jsonify(_report_row_to_dict(row, conn))


@app.route("/api/reports/by-ticket/<ticket_id>", methods=["GET"])
@login_required()
def api_get_report_by_ticket(ticket_id):
    """Convenience endpoint — look up by the human-readable ticket ID (e.g. CC-2026-101)."""
    with get_db() as conn:
        row = _find_report_row(conn, ticket_id)

        if not row:
            return jsonify({"error": "Report not found."}), 404

        if session["role"] == "student" and row["user_id"] != session["user_id"]:
            return jsonify({"error": "Access denied."}), 403

        return jsonify(_report_row_to_dict(row, conn))


@app.route("/api/reports", methods=["POST"])
@login_required(role="student")
def api_create_report():
    """Create a new report. Requires live site photo and GPS coordinates."""
    user_id = session["user_id"]

    # Support form submissions (multipart or urlencoded) and JSON
    if request.form:
        data = request.form
    else:
        data = request.get_json(silent=True) or {}

    title       = (data.get("title") or "").strip()
    category    = (data.get("category") or "").strip()
    building    = (data.get("building") or "").strip()
    floor       = (data.get("floor") or "").strip()
    room        = (data.get("roomArea") or data.get("room") or "").strip()
    description = (data.get("description") or "").strip()
    priority    = (data.get("priority") or "Medium").strip()

    if not title or not category or not description or not building:
        return jsonify({"error": "Title, category, building, and description are required."}), 400

    # 1. Text quality checks (title and description) BEFORE processing or saving photo
    hard_error, soft_flags = check_text_quality(title, description)
    if hard_error:
        return jsonify({"error": hard_error}), 400

    text_flagged = 1 if soft_flags else 0
    text_flag_reason = "; ".join(soft_flags) if soft_flags else None
    trust_level = "low" if text_flagged else "high"

    # 2. Validate mandatory photo_source ('camera' or 'upload')
    photo_source = (data.get("photo_source") or "").strip().lower()
    if photo_source not in ("camera", "upload"):
        return jsonify({"error": "photo_source is required and must be either 'camera' or 'upload'."}), 400

    # 3. Validate mandatory site photo file
    file = request.files.get("image")
    if not file or not file.filename:
        return jsonify({"error": "A site photo is required for all new reports."}), 400

    detected_ext = _detect_image_type(file)
    if photo_source == "camera":
        if detected_ext != "jpg":
            return jsonify({"error": "Camera photos must be valid JPEG images."}), 400
    else:  # upload
        if detected_ext not in ("jpg", "png"):
            return jsonify({"error": "Uploaded photos must be valid JPEG or PNG images."}), 400

    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size == 0:
        return jsonify({"error": "Uploaded photo file is empty."}), 400
    if file_size > MAX_IMAGE_SIZE:
        return jsonify({"error": "Photo file exceeds maximum limit of 10MB."}), 400

    # 3. Validate mandatory GPS coordinates & accuracy
    lat_raw = data.get("latitude")
    lng_raw = data.get("longitude")
    acc_raw = data.get("location_accuracy") if data.get("location_accuracy") is not None else data.get("locationAccuracy")

    if lat_raw is None or lng_raw is None or acc_raw is None or str(lat_raw).strip() == "" or str(lng_raw).strip() == "" or str(acc_raw).strip() == "":
        return jsonify({"error": "Live GPS coordinates (latitude, longitude, and accuracy) are required."}), 400

    try:
        lat = float(lat_raw)
        lng = float(lng_raw)
        acc = float(acc_raw)
    except (ValueError, TypeError):
        return jsonify({"error": "Latitude, longitude, and accuracy must be valid numeric values."}), 400

    if math.isnan(lat) or math.isinf(lat) or math.isnan(lng) or math.isinf(lng) or math.isnan(acc) or math.isinf(acc):
        return jsonify({"error": "Coordinates and accuracy must be finite numbers."}), 400

    if not (-90.0 <= lat <= 90.0):
        return jsonify({"error": "Latitude must be between -90 and 90 degrees."}), 400

    if not (-180.0 <= lng <= 180.0):
        return jsonify({"error": "Longitude must be between -180 and 180 degrees."}), 400

    if acc < 0:
        return jsonify({"error": "Location accuracy must be a non-negative number."}), 400

    # 4. Save photo securely with server-generated random UUID filename and detected extension
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{detected_ext}"
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    image_url = f"/static/uploads/{filename}"

    # 5. Server-generated capture timestamp (never trust client)
    photo_captured_at = datetime.utcnow().isoformat()

    with get_db() as conn:
        # Generate ticket ID: CC-YYYY-<next sequential number>
        max_id = conn.execute("SELECT COALESCE(MAX(id), 0) FROM reports").fetchone()[0]
        year = datetime.utcnow().year
        ticket_id = f"CC-{year}-{100 + max_id + 1}"
        while conn.execute("SELECT 1 FROM reports WHERE ticket_id = ?", (ticket_id,)).fetchone():
            max_id += 1
            ticket_id = f"CC-{year}-{100 + max_id + 1}"

        cursor = conn.execute(
            """INSERT INTO reports
               (ticket_id, user_id, title, category, building, floor, room,
                description, priority, status, image_url, latitude, longitude,
                location_accuracy, photo_captured_at, photo_source,
                text_flagged, text_flag_reason, trust_level)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Reported', ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (ticket_id, user_id, title, category, building, floor, room,
             description, priority, image_url, lat, lng, acc, photo_captured_at, photo_source,
             text_flagged, text_flag_reason, trust_level),
        )
        report_id = cursor.lastrowid

        # Seed the initial audit history entry
        reporter = conn.execute(
            "SELECT name FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        action_note = f"Issue reported by {reporter['name']} with live camera photo." if photo_source == "camera" else f"Issue reported by {reporter['name']} with uploaded photo."
        conn.execute(
            """INSERT INTO report_history (report_id, user_id, action, note)
               VALUES (?, ?, 'Reported', ?)""",
            (report_id, user_id, action_note),
        )

        # Dispatch async email confirmation to report owner
        notify_report_submitted(report_id, ticket_id, user_id, title)

        row = conn.execute(
            "SELECT * FROM reports WHERE id = ?", (report_id,)
        ).fetchone()
        return jsonify(_report_row_to_dict(row, conn)), 201


@app.route("/api/reports/<int:report_db_id>/status", methods=["PATCH", "PUT"])
@app.route("/api/reports/<ticket_id>/status", methods=["PATCH", "PUT"])
@login_required(role="admin")
def api_update_report_status(report_db_id=None, ticket_id=None):
    """Update report status and log action into report_history."""
    target = report_db_id if report_db_id is not None else ticket_id
    data = request.get_json(silent=True) or {}
    new_status = data.get("status", "").strip()
    note = data.get("note", "").strip()

    valid_statuses = ["Reported", "Assigned", "In Progress", "Resolved", "Closed", "Rejected"]
    if new_status not in valid_statuses:
        return jsonify({"error": f"Invalid status: {new_status}"}), 400

    with get_db() as conn:
        row = _find_report_row(conn, target)
        if not row:
            return jsonify({"error": "Report not found."}), 404

        real_db_id = row["id"]
        action_note = note if note else f"Status updated to {new_status}."
        conn.execute(
            """UPDATE reports
               SET status = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (new_status, real_db_id),
        )
        conn.execute(
            """INSERT INTO report_history (report_id, user_id, action, note)
               VALUES (?, ?, ?, ?)""",
            (real_db_id, session["user_id"], new_status, action_note),
        )

        # Dispatch async email notifications for report updates
        if row["status"] != new_status:
            if new_status == "Rejected":
                notify_report_rejected(real_db_id, row["ticket_id"], row["user_id"], row["title"], action_note)
            elif new_status in ("In Progress", "Resolved"):
                notify_status_changed(real_db_id, row["ticket_id"], row["user_id"], row["title"], new_status)

        updated_row = conn.execute("SELECT * FROM reports WHERE id = ?", (real_db_id,)).fetchone()
        return jsonify(_report_row_to_dict(updated_row, conn))


@app.route("/api/reports/<int:report_db_id>/assign", methods=["PATCH", "PUT"])
@app.route("/api/reports/<ticket_id>/assign", methods=["PATCH", "PUT"])
@login_required(role="admin")
def api_assign_report_team(report_db_id=None, ticket_id=None):
    """Assign maintenance team, change status to Assigned if Reported, and log history."""
    target = report_db_id if report_db_id is not None else ticket_id
    data = request.get_json(silent=True) or {}
    team = data.get("team", "").strip()
    note = data.get("note", "").strip()

    if not team:
        return jsonify({"error": "Team name is required."}), 400

    with get_db() as conn:
        row = _find_report_row(conn, target)
        if not row:
            return jsonify({"error": "Report not found."}), 404

        real_db_id = row["id"]
        new_status = "Assigned" if row["status"] == "Reported" else row["status"]
        action_note = note if note else f"Assigned to {team}."

        conn.execute(
            """UPDATE reports
               SET assigned_team = ?, status = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (team, new_status, real_db_id),
        )
        conn.execute(
            """INSERT INTO report_history (report_id, user_id, action, note)
               VALUES (?, ?, 'Assigned', ?)""",
            (real_db_id, session["user_id"], action_note),
        )

        # Dispatch async email notification for team assignment
        notify_team_assigned(real_db_id, row["ticket_id"], row["user_id"], row["title"], team)

        updated_row = conn.execute("SELECT * FROM reports WHERE id = ?", (real_db_id,)).fetchone()
        return jsonify(_report_row_to_dict(updated_row, conn))


@app.route("/api/reports/<int:report_db_id>/history", methods=["GET"])
@app.route("/api/reports/<ticket_id>/history", methods=["GET"])
@login_required()
def api_get_report_history(report_db_id=None, ticket_id=None):
    """Fetch report audit history entries."""
    target = report_db_id if report_db_id is not None else ticket_id
    with get_db() as conn:
        report = _find_report_row(conn, target)
        if not report:
            return jsonify({"error": "Report not found."}), 404

        if session["role"] == "student" and report["user_id"] != session["user_id"]:
            return jsonify({"error": "Access denied."}), 403

        real_db_id = report["id"]
        history_rows = conn.execute(
            """SELECT h.id, h.action, h.note, h.created_at, u.name as user_name, u.role as user_role
               FROM report_history h
               LEFT JOIN users u ON h.user_id = u.id
               WHERE h.report_id = ?
               ORDER BY h.created_at ASC""",
            (real_db_id,),
        ).fetchall()

        history = [{
            "id": h["id"],
            "timestamp": h["created_at"],
            "status": h["action"],
            "note": h["note"] or "",
            "updatedBy": f"{h['user_name']} ({'Admin' if h['user_role'] == 'admin' else 'Student'})" if h["user_name"] else "System",
        } for h in history_rows]

        return jsonify(history)


@app.route("/api/reports/<int:report_db_id>", methods=["DELETE"])
@app.route("/api/reports/<ticket_id>", methods=["DELETE"])
@login_required(role="admin")
def api_delete_report(report_db_id=None, ticket_id=None):
    """Delete a report along with its associated history and feedback (Admin only)."""
    target = report_db_id if report_db_id is not None else ticket_id
    with get_db() as conn:
        row = _find_report_row(conn, target)
        if not row:
            return jsonify({"error": "Report not found."}), 404

        real_db_id = row["id"]
        # Delete related feedback
        conn.execute("DELETE FROM feedback WHERE report_id = ?", (real_db_id,))
        # Delete related history
        conn.execute("DELETE FROM report_history WHERE report_id = ?", (real_db_id,))
        # Clean up or detach related email logs
        conn.execute("DELETE FROM email_log WHERE report_id = ?", (real_db_id,))
        # Delete report
        conn.execute("DELETE FROM reports WHERE id = ?", (real_db_id,))

        return jsonify({"message": f"Report {row['ticket_id']} successfully deleted.", "id": row["ticket_id"]})


# ---------------------------------------------------------------------------
# Feedback API
# ---------------------------------------------------------------------------

@app.route("/api/feedback", methods=["POST"])
@login_required(role="student")
def api_submit_feedback():
    """Submit star rating + comment for a resolved report. One per report."""
    data = request.get_json(silent=True) or {}
    report_db_id = data.get("reportId")
    rating       = data.get("rating")
    comments     = (data.get("comments") or "").strip()

    if not report_db_id or rating is None:
        return jsonify({"error": "reportId and rating are required."}), 400

    try:
        rating = int(rating)
    except (ValueError, TypeError):
        return jsonify({"error": "Rating must be an integer."}), 400

    if not (1 <= rating <= 5):
        return jsonify({"error": "Rating must be between 1 and 5."}), 400

    with get_db() as conn:
        report = _find_report_row(conn, report_db_id)
        if not report:
            return jsonify({"error": "Report not found."}), 404

        real_db_id = report["id"]

        # Students can only submit feedback on their own reports
        if report["user_id"] != session["user_id"]:
            return jsonify({"error": "Access denied."}), 403

        if report["status"] not in ("Resolved", "Closed"):
            return jsonify({"error": "Feedback can only be submitted for resolved or closed reports."}), 409

        # Check if feedback already exists
        existing = conn.execute(
            "SELECT id FROM feedback WHERE report_id = ?", (real_db_id,)
        ).fetchone()
        if existing:
            return jsonify({"error": "Feedback already submitted for this report."}), 409

        conn.execute(
            """INSERT INTO feedback (report_id, user_id, rating, comments)
               VALUES (?, ?, ?, ?)""",
            (real_db_id, session["user_id"], rating, comments or None),
        )

        # Auto-close report on feedback submission
        conn.execute(
            """UPDATE reports SET status = 'Closed', updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (real_db_id,),
        )
        conn.execute(
            """INSERT INTO report_history (report_id, user_id, action, note)
               VALUES (?, ?, 'Closed', ?)""",
            (real_db_id, session["user_id"], f"Student submitted feedback (rating: {rating}/5)."),
        )

        return jsonify({"message": "Feedback submitted successfully.", "rating": rating}), 201


@app.route("/api/feedback", methods=["GET"])
@login_required()
def api_get_feedback():
    """Return feedback entries.
    Admins get all. Students get only their own (filtered by their reports).
    Optional ?reportId=<int> to filter to a single report.
    Optional ?limit=<int> to restrict number of entries returned."""
    report_id_filter = request.args.get("reportId", type=int)
    limit = request.args.get("limit", type=int)

    with get_db() as conn:
        query  = """
            SELECT f.id, f.report_id, f.rating, f.comments, f.created_at,
                   r.ticket_id, r.title, r.category,
                   u.name as reviewer_name
            FROM feedback f
            JOIN reports r ON f.report_id = r.id
            JOIN users   u ON f.user_id   = u.id
            WHERE 1=1
        """
        params = []

        if session["role"] == "student":
            query  += " AND r.user_id = ?"
            params.append(session["user_id"])

        if report_id_filter:
            query  += " AND f.report_id = ?"
            params.append(report_id_filter)

        query += " ORDER BY f.created_at DESC"

        if limit and limit > 0:
            query += f" LIMIT {int(limit)}"

        rows   = conn.execute(query, params).fetchall()

    result = [{
        "id":           row["id"],
        "reportId":     row["report_id"],
        "ticketId":     row["ticket_id"],
        "reportTitle":  row["title"],
        "category":     row["category"],
        "rating":       row["rating"],
        "comments":     row["comments"],
        "reviewerName": row["reviewer_name"],
        "createdAt":    row["created_at"],
    } for row in rows]

    return jsonify(result)


# ---------------------------------------------------------------------------
# Profile API
# ---------------------------------------------------------------------------

@app.route("/api/profile", methods=["GET"])
@login_required()
def api_get_profile():
    """Return the current user's full profile."""
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()

    if not user:
        session.clear()
        return jsonify({"error": "User not found."}), 404

    return jsonify(_user_payload(user))


@app.route("/api/profile", methods=["PUT", "PATCH"])
@login_required()
def api_update_profile():
    """Update name, phone, department, and identifier. Email/role are immutable."""
    data = request.get_json(silent=True) or {}

    name       = (data.get("name") or "").strip()
    phone      = (data.get("phone") or "").strip()
    department = (data.get("department") or "").strip()
    identifier = (data.get("identifier") or "").strip()

    raw_notif = data.get("emailNotifications") if "emailNotifications" in data else data.get("email_notifications")
    email_notif = None
    if raw_notif is not None:
        email_notif = 1 if raw_notif in (True, 1, "1", "true", "True") else 0

    if not name:
        return jsonify({"error": "Name cannot be empty."}), 400

    with get_db() as conn:
        if email_notif is not None:
            conn.execute(
                """UPDATE users SET name = ?, phone = ?, department = ?, identifier = ?, email_notifications = ?
                   WHERE id = ?""",
                (name, phone or None, department or None, identifier or None, email_notif, session["user_id"]),
            )
        else:
            conn.execute(
                """UPDATE users SET name = ?, phone = ?, department = ?, identifier = ?
                   WHERE id = ?""",
                (name, phone or None, department or None, identifier or None, session["user_id"]),
            )
        user = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()

    return jsonify(_user_payload(user))


# ---------------------------------------------------------------------------
# Uploaded photo serving (Authenticated & Ownership guarded)
# ---------------------------------------------------------------------------

@app.route("/static/uploads/<filename>")
@login_required()
def serve_uploaded_photo(filename):
    """Serve uploaded photos only to authenticated users:
    - Admins can view any site photo.
    - Students can only view photos attached to their own reports.
    - Unauthenticated requests are rejected.
    """
    safe_name = secure_filename(filename)
    with get_db() as conn:
        report = conn.execute(
            "SELECT user_id FROM reports WHERE image_url LIKE ?",
            (f"%{safe_name}",)
        ).fetchone()

    if report:
        if session.get("role") != "admin" and report["user_id"] != session.get("user_id"):
            return jsonify({"error": "Access denied."}), 403
    else:
        file_path = os.path.join(UPLOAD_FOLDER, safe_name)
        if not os.path.exists(file_path):
            return jsonify({"error": "Photo not found."}), 404
        if session.get("role") != "admin":
            return jsonify({"error": "Access denied."}), 403

    return send_from_directory(UPLOAD_FOLDER, safe_name)


# ---------------------------------------------------------------------------
# Protected page routes  (explicit — each carries the correct role guard)
# ---------------------------------------------------------------------------

@app.route("/student-dashboard")
@app.route("/student-dashboard.html")
@login_required(role="student")
def student_dashboard():
    return render_template("student-dashboard.html")


@app.route("/report-problem")
@app.route("/report-problem.html")
@login_required(role="student")
def report_problem():
    return render_template("report-problem.html")


@app.route("/my-reports")
@app.route("/my-reports.html")
@login_required(role="student")
def my_reports():
    return render_template("my-reports.html")


@app.route("/report-details")
@app.route("/report-details.html")
@login_required()
def report_details():
    return render_template("report-details.html")


@app.route("/admin-dashboard")
@app.route("/admin-dashboard.html")
@login_required(role="admin")
def admin_dashboard():
    return render_template("admin-dashboard.html")


@app.route("/admin-issues")
@app.route("/admin-issues.html")
@login_required(role="admin")
def admin_issues():
    return render_template("admin-issues.html")


@app.route("/feedback")
@app.route("/feedback.html")
@login_required(role="admin")
def feedback():
    return render_template("feedback.html")


@app.route("/profile")
@app.route("/profile.html")
@login_required()
def profile():
    return render_template("profile.html")


init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(debug=True, port=port)
