import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "instance" / "campus_care.db"


def get_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('student', 'admin')),
                identifier TEXT,
                department TEXT,
                phone TEXT,
                email_notifications INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT UNIQUE,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                building TEXT NOT NULL,
                floor TEXT,
                room TEXT,
                description TEXT NOT NULL,
                priority TEXT NOT NULL DEFAULT 'Medium',
                status TEXT NOT NULL DEFAULT 'Reported',
                assigned_team TEXT,
                image_url TEXT,
                latitude REAL,
                longitude REAL,
                location_accuracy REAL,
                photo_captured_at TEXT,
                photo_source TEXT,
                text_flagged INTEGER DEFAULT 0,
                text_flag_reason TEXT,
                trust_level TEXT DEFAULT 'high',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS report_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER NOT NULL,
                user_id INTEGER,
                action TEXT NOT NULL,
                note TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (report_id) REFERENCES reports(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER NOT NULL UNIQUE,
                user_id INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                comments TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (report_id) REFERENCES reports(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS maintenance_teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS email_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER,
                to_email TEXT NOT NULL,
                event TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('sent', 'failed', 'skipped')),
                error TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (report_id) REFERENCES reports(id)
            );
        """)

        # Seed categories (INSERT OR IGNORE so re-runs are safe)
        categories = [
            "Electrical",
            "Plumbing",
            "Housekeeping",
            "IT / Network",
            "Furniture",
            "Security",
            "Air Conditioning",
            "Other",
        ]
        conn.executemany(
            "INSERT OR IGNORE INTO categories (name) VALUES (?)",
            [(c,) for c in categories],
        )

        # Seed maintenance teams
        teams = [
            "Electrical Team",
            "Plumbing Team",
            "Housekeeping Team",
            "IT Support Team",
            "Carpentry & Furniture Team",
            "Security Team",
            "HVAC Team",
            "General Maintenance",
        ]
        conn.executemany(
            "INSERT OR IGNORE INTO maintenance_teams (name) VALUES (?)",
            [(t,) for t in teams],
        )

        # Migration guard: Add missing columns to existing reports and users tables
        # (ALTER TABLE IF NOT EXISTS is not supported in SQLite, so we check table_info first).
        user_cols = [row[1] for row in conn.execute("PRAGMA table_info(users)")]
        if "email_notifications" not in user_cols:
            conn.execute("ALTER TABLE users ADD COLUMN email_notifications INTEGER DEFAULT 1")

        cols = [row[1] for row in conn.execute("PRAGMA table_info(reports)")]
        migrations = [
            ("image_url", "TEXT"),
            ("latitude", "REAL"),
            ("longitude", "REAL"),
            ("location_accuracy", "REAL"),
            ("photo_captured_at", "TEXT"),
            ("photo_source", "TEXT"),
            ("text_flagged", "INTEGER DEFAULT 0"),
            ("text_flag_reason", "TEXT"),
            ("trust_level", "TEXT DEFAULT 'high'"),
        ]
        for col_name, col_type in migrations:
            if col_name not in cols:
                conn.execute(f"ALTER TABLE reports ADD COLUMN {col_name} {col_type}")


if __name__ == "__main__":
    init_db()
    print(f"Database initialized: {DB_PATH}")
