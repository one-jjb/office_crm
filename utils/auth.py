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


def get_user_by_username(username):
    conn = sqlite3.connect(DB_PATH)
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

    user_id, username, name, role = user

    return {
        "id": user_id,
        "username": username,
        "name": name,
        "role": role
    }


def get_user_by_id(user_id):
    conn = sqlite3.connect(DB_PATH)
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

    user_id, username, name, role = user

    return {
        "id": user_id,
        "username": username,
        "name": name,
        "role": role
    }


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


def get_authenticator_credentials():
    """
    streamlit-authenticator가 사용할 credentials dict를 DB users 테이블에서 생성합니다.
    기존 password_hash 값을 그대로 사용합니다.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            username,
            password_hash,
            name
        FROM users
    """)

    rows = cursor.fetchall()
    conn.close()

    credentials = {
        "usernames": {}
    }

    for row in rows:
        username = row["username"]

        credentials["usernames"][username] = {
            "name": row["name"],
            "password": row["password_hash"]
        }

    return credentials