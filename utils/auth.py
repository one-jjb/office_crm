import sqlite3
import bcrypt
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "db" / "crm.db"


def create_user(username, password, name, role="staff"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    password_hash = bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()

    cursor.execute("""
        INSERT INTO users
        (username, password_hash, name, role)
        VALUES (?, ?, ?, ?)
    """, (username, password_hash, name, role))

    conn.commit()
    conn.close()


def verify_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, username, password_hash, name, role
        FROM users
        WHERE username = ?
    """, (username,))

    user = cursor.fetchone()
    conn.close()

    if not user:
        return None

    user_id, username, password_hash, name, role = user

    if bcrypt.checkpw(password.encode(), password_hash.encode()):
        return {
            "id": user_id,
            "username": username,
            "name": name,
            "role": role
        }

    return None


def get_users():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            username,
            name,
            role,
            created_at
        FROM users
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]