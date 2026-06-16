import sqlite3
import bcrypt
import secrets
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "db" / "crm.db"

SESSION_DAYS = 30


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_login_sessions_table():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS login_sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


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


def create_login_session(user_id):
    ensure_login_sessions_table()

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(days=SESSION_DAYS)

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO login_sessions
        (token, user_id, expires_at)
        VALUES (?, ?, ?)
    """, (
        token,
        user_id,
        expires_at.isoformat()
    ))

    conn.commit()
    conn.close()

    return token


def get_user_by_session_token(token):
    if not token:
        return None

    ensure_login_sessions_table()

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            u.id,
            u.username,
            u.name,
            u.role,
            s.expires_at
        FROM login_sessions s
        JOIN users u ON u.id = s.user_id
        WHERE s.token = ?
    """, (token,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    expires_at = datetime.fromisoformat(row["expires_at"])

    if expires_at < datetime.now():
        delete_login_session(token)
        return None

    return {
        "id": row["id"],
        "username": row["username"],
        "name": row["name"],
        "role": row["role"]
    }


def delete_login_session(token):
    if not token:
        return

    ensure_login_sessions_table()

    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM login_sessions
        WHERE token = ?
    """, (token,))

    conn.commit()
    conn.close()


def restore_user_from_session():
    if "user" not in st_session_keys():
        pass

    token = None

    try:
        token = st_query_get("sid")
    except Exception:
        token = None

    if not token:
        return False

    user = get_user_by_session_token(token)

    if not user:
        return False

    import streamlit as st
    st.session_state.user = user
    st.session_state.session_token = token

    return True


def st_query_get(key):
    import streamlit as st

    value = st.query_params.get(key)

    if isinstance(value, list):
        return value[0] if value else None

    return value


def st_session_keys():
    import streamlit as st
    return st.session_state.keys()