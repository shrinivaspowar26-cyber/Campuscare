from getpass import getpass
from werkzeug.security import generate_password_hash
from database import get_db, init_db

init_db()

name = input("Admin name: ").strip()
email = input("Admin email: ").strip().lower()
password = getpass("Admin password (minimum 8 characters): ")

if not name or not email or len(password) < 8:
    raise SystemExit("Name, email, and a password of at least 8 characters are required.")

with get_db() as conn:
    existing = conn.execute(
        "SELECT id FROM users WHERE email = ?", (email,)
    ).fetchone()

    if existing:
        raise SystemExit("That email already exists.")

    conn.execute("""
        INSERT INTO users (name, email, password_hash, role, identifier, department, phone)
        VALUES (?, ?, ?, 'admin', 'ADMIN', 'Facilities', '')
    """, (name, email, generate_password_hash(password)))

print("Admin account created.")
