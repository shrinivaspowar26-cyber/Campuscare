import os
import re
import smtplib
import threading
from email.message import EmailMessage
from datetime import datetime
from database import get_db

DEV_LOG_FILE = os.path.join(os.path.dirname(__file__), "instance", "email_dev.log")


def get_smtp_config():
    """Retrieve SMTP and app configuration dynamically from environment variables."""
    host = os.environ.get("SMTP_HOST", "").strip()
    port = int(os.environ.get("SMTP_PORT", 587))
    user = os.environ.get("SMTP_USER", "").strip()
    password = os.environ.get("SMTP_PASSWORD", "").strip()
    mail_from = os.environ.get("MAIL_FROM", user or "no-reply@campuscare.local").strip()
    base_url = os.environ.get("APP_BASE_URL", "http://127.0.0.1:5001").rstrip("/")
    dev_mode = not (host and user and password)

    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "mail_from": mail_from,
        "base_url": base_url,
        "dev_mode": dev_mode,
    }


def _clean_subject_line(subject):
    """Strip newlines, carriage returns, and leading/trailing whitespace to prevent header injection."""
    return re.sub(r"[\r\n]+", " ", str(subject or "")).strip()


def _send_worker(report_id, user_id, event, subject, body):
    """Worker executed in a background thread to deliver or log emails.

    Catches all exceptions to ensure API calls are never blocked or failed.
    """
    config = get_smtp_config()
    to_email = None

    # 1. Fetch user email and notification preference
    try:
        with get_db() as conn:
            user = conn.execute(
                "SELECT email, email_notifications FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
            if not user or not user["email"]:
                print(f"[mailer] No recipient email found for user_id={user_id}")
                return
            to_email = user["email"]

            # If user has opted out of email notifications, log as skipped and return
            user_prefs = user["email_notifications"] if "email_notifications" in user.keys() else 1
            if user_prefs == 0:
                conn.execute(
                    """INSERT INTO email_log (report_id, to_email, event, status, error)
                       VALUES (?, ?, ?, 'skipped', 'User opted out of email notifications')""",
                    (report_id, to_email, event),
                )
                print(f"[mailer] Email skipped for {to_email} (notifications disabled)")
                return
    except Exception as e:
        print(f"[mailer] Database error reading user preference: {e}")
        return

    clean_subject = _clean_subject_line(subject)

    # 2. Dev mode: output email to console and dev log file
    if config["dev_mode"]:
        log_entry = (
            f"\n==================== [DEV MODE EMAIL NOTIFICATION] ====================\n"
            f"Timestamp: {datetime.utcnow().isoformat()}Z\n"
            f"Event:     {event}\n"
            f"Report ID: {report_id}\n"
            f"To:        {to_email}\n"
            f"From:      {config['mail_from']}\n"
            f"Subject:   {clean_subject}\n"
            f"------------------------------------------------------------------------\n"
            f"{body}\n"
            f"========================================================================\n"
        )
        print(log_entry)

        try:
            os.makedirs(os.path.dirname(DEV_LOG_FILE), exist_ok=True)
            with open(DEV_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as log_err:
            print(f"[mailer] Could not append to dev log file: {log_err}")

        # Record dev email in database as sent
        try:
            with get_db() as conn:
                conn.execute(
                    """INSERT INTO email_log (report_id, to_email, event, status, error)
                       VALUES (?, ?, ?, 'sent', NULL)""",
                    (report_id, to_email, event),
                )
        except Exception as db_err:
            print(f"[mailer] Database error recording dev email_log: {db_err}")
        return

    # 3. Live mode: connect to SMTP server with STARTTLS and timeout
    msg = EmailMessage()
    msg["Subject"] = clean_subject
    msg["From"] = config["mail_from"]
    msg["To"] = to_email
    msg.set_content(body)

    try:
        with smtplib.SMTP(config["host"], config["port"], timeout=10) as server:
            server.starttls()
            server.login(config["user"], config["password"])
            server.send_message(msg)

        # Record success
        with get_db() as conn:
            conn.execute(
                """INSERT INTO email_log (report_id, to_email, event, status, error)
                   VALUES (?, ?, ?, 'sent', NULL)""",
                (report_id, to_email, event),
            )
        print(f"[mailer] Email successfully sent to {to_email} (event={event})")

    except Exception as exc:
        err_msg = str(exc)
        print(f"[mailer] SMTP delivery failed to {to_email}: {err_msg}")
        try:
            with get_db() as conn:
                conn.execute(
                    """INSERT INTO email_log (report_id, to_email, event, status, error)
                       VALUES (?, ?, ?, 'failed', ?)""",
                    (report_id, to_email, event, err_msg),
                )
        except Exception as db_err:
            print(f"[mailer] Database error recording email_log failure: {db_err}")


def send_email_async(report_id, user_id, event, subject, body):
    """Send email asynchronously in a background thread."""
    thread = threading.Thread(
        target=_send_worker,
        args=(report_id, user_id, event, subject, body),
        daemon=True,
    )
    thread.start()
    return thread


# ---------------------------------------------------------------------------
# Specific Event Notification Helpers
# ---------------------------------------------------------------------------

def notify_report_submitted(report_id, ticket_id, user_id, title):
    """Send confirmation email when a report is created."""
    config = get_smtp_config()
    clean_title = _clean_subject_line(title)
    subject = f"[Campus Care] Issue Report Received: {clean_title} ({ticket_id})"
    report_url = f"{config['base_url']}/report-details?id={ticket_id}"

    body = (
        f"Hello,\n\n"
        f"Your facility problem report has been successfully received and submitted.\n\n"
        f"Ticket ID: {ticket_id}\n"
        f"Title:     {clean_title}\n"
        f"Status:    Reported (Awaiting review & triage)\n\n"
        f"You can track the progress of your repair at:\n"
        f"{report_url}\n\n"
        f"Thank you for helping keep our campus safe and clean!\n"
        f"— Campus Care Facilities Team"
    )

    return send_email_async(report_id, user_id, "report_submitted", subject, body)


def notify_team_assigned(report_id, ticket_id, user_id, title, team_name):
    """Send email when a maintenance team is assigned to the report."""
    config = get_smtp_config()
    clean_title = _clean_subject_line(title)
    subject = f"[Campus Care] Maintenance Team Assigned: {clean_title} ({ticket_id})"
    report_url = f"{config['base_url']}/report-details?id={ticket_id}"

    body = (
        f"Hello,\n\n"
        f"A maintenance crew has been assigned to your reported issue.\n\n"
        f"Ticket ID:     {ticket_id}\n"
        f"Title:         {clean_title}\n"
        f"Assigned Team: {team_name}\n"
        f"Status:        Assigned\n\n"
        f"You can view technician notes and updates at:\n"
        f"{report_url}\n\n"
        f"— Campus Care Facilities Team"
    )

    return send_email_async(report_id, user_id, "team_assigned", subject, body)


def notify_status_changed(report_id, ticket_id, user_id, title, new_status):
    """Send email when status changes to In Progress or Resolved."""
    config = get_smtp_config()
    clean_title = _clean_subject_line(title)
    subject = f"[Campus Care] Status Update ({new_status}): {clean_title} ({ticket_id})"
    report_url = f"{config['base_url']}/report-details?id={ticket_id}"

    status_message = ""
    if new_status == "Resolved":
        status_message = (
            "The maintenance crew has completed work on this issue and marked it as Resolved.\n"
            "Please take a moment to visit your report link and submit your rating and feedback!"
        )
    elif new_status == "In Progress":
        status_message = "A technician is actively working on resolving this issue."
    else:
        status_message = f"Your report status has transitioned to: {new_status}."

    body = (
        f"Hello,\n\n"
        f"There is an update on your campus problem report.\n\n"
        f"Ticket ID:  {ticket_id}\n"
        f"Title:      {clean_title}\n"
        f"New Status: {new_status}\n\n"
        f"{status_message}\n\n"
        f"View report details:\n"
        f"{report_url}\n\n"
        f"— Campus Care Facilities Team"
    )

    return send_email_async(report_id, user_id, "status_changed", subject, body)


def notify_report_rejected(report_id, ticket_id, user_id, title, reason):
    """Send email when an issue report is marked as Rejected by an administrator."""
    config = get_smtp_config()
    clean_title = _clean_subject_line(title)
    subject = f"[Campus Care] Report Update (Rejected): {clean_title} ({ticket_id})"
    report_url = f"{config['base_url']}/report-details?id={ticket_id}"

    body = (
        f"Hello,\n\n"
        f"Your campus problem report could not be processed and has been marked as Rejected.\n\n"
        f"Ticket ID:        {ticket_id}\n"
        f"Title:            {clean_title}\n"
        f"Rejection Reason: {reason or 'Issue is invalid, duplicated, or outside facility maintenance scope.'}\n\n"
        f"You can review technician remarks and details at:\n"
        f"{report_url}\n\n"
        f"— Campus Care Facilities Team"
    )

    return send_email_async(report_id, user_id, "report_rejected", subject, body)
