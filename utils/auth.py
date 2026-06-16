import sqlite3
import bcrypt
from pathlib import Path

import streamlit as st
import streamlit_authenticator as stauth

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "db" / "crm.db"

COOKIE_NAME = "office_crm_auth"
COOKIE_KEY = "office_crm_cookie_signature_key_v1"
COOKIE_EXPIRY_DAYS = 30


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


def make_authenticator():
    """
    모든 페이지에서 동일한 설정으로 authenticator를 생성합니다.
    """
    credentials = get_authenticator_credentials()

    authenticator = stauth.Authenticate(
        credentials,
        COOKIE_NAME,
        COOKIE_KEY,
        COOKIE_EXPIRY_DAYS
    )

    st.session_state.authenticator = authenticator

    return authenticator


def sync_user_from_authenticator():
    """
    streamlit-authenticator의 세션 상태를 기존 CRM의 st.session_state.user 구조로 맞춥니다.
    """
    auth_status = st.session_state.get("authentication_status")
    username = st.session_state.get("username")

    if auth_status is True and username:
        user = get_user_by_username(username)

        if user:
            st.session_state.user = user
            return True

    if "user" not in st.session_state:
        st.session_state.user = None

    return False


def restore_authentication():
    """
    새로고침 후 페이지가 직접 실행될 때도 쿠키 인증 복구를 시도합니다.

    streamlit-authenticator는 login() 호출 시 쿠키를 확인해
    st.session_state.authentication_status / username 값을 복구합니다.
    """
    authenticator = make_authenticator()

    try:
        authenticator.login(
            location="unrendered"
        )
    except TypeError:
        try:
            authenticator.login("로그인", "main")
        except Exception:
            pass
    except Exception:
        pass

    return sync_user_from_authenticator()