import sqlite3
import bcrypt
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "db" / "crm.db"

REMEMBER_DAYS = 30


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_remembered_login_table():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS remembered_login (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            user_id INTEGER NOT NULL,
            expires_at TEXT NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


def create_user(username, password, name, role="staff"):
    conn = get_conn()
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
    conn = get_conn()
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

    if bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return {
            "id": user["id"],
            "username": user["username"],
            "name": user["name"],
            "role": user["role"]
        }

    return None


def get_user_by_id(user_id):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, username, name, role
        FROM users
        WHERE id = ?
    """, (user_id,))

    user = cursor.fetchone()
    conn.close()

    if not user:
        return None

    return dict(user)


def get_user_by_username(username):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, username, name, role
        FROM users
        WHERE username = ?
    """, (username,))

    user = cursor.fetchone()
    conn.close()

    if not user:
        return None

    return dict(user)


def get_users():
    conn = get_conn()
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


def remember_login(user_id):
    ensure_remembered_login_table()

    expires_at = datetime.now() + timedelta(days=REMEMBER_DAYS)

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO remembered_login
        (id, user_id, expires_at, updated_at)
        VALUES (1, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(id) DO UPDATE SET
            user_id = excluded.user_id,
            expires_at = excluded.expires_at,
            updated_at = CURRENT_TIMESTAMP
    """, (
        user_id,
        expires_at.isoformat()
    ))

    conn.commit()
    conn.close()


def restore_remembered_login():
    ensure_remembered_login_table()

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            user_id,
            expires_at
        FROM remembered_login
        WHERE id = 1
    """)

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    expires_at = datetime.fromisoformat(row["expires_at"])

    if expires_at < datetime.now():
        clear_remembered_login()
        return None

    return get_user_by_id(row["user_id"])


def clear_remembered_login():
    ensure_remembered_login_table()

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM remembered_login
        WHERE id = 1
    """)

    conn.commit()
    conn.close()