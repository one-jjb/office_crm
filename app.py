import streamlit as st
import streamlit_authenticator as stauth

from utils.auth import (
    get_authenticator_credentials,
    get_user_by_username,
)


st.set_page_config(
    page_title="사무실 CRM",
    layout="wide"
)


COOKIE_NAME = "office_crm_auth"
COOKIE_KEY = "office_crm_cookie_signature_key_v1"
COOKIE_EXPIRY_DAYS = 30


def hide_sidebar_before_login():
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            display: none;
        }
        [data-testid="stSidebarNav"] {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def make_authenticator():
    credentials = get_authenticator_credentials()

    authenticator = stauth.Authenticate(
        credentials,
        COOKIE_NAME,
        COOKIE_KEY,
        COOKIE_EXPIRY_DAYS
    )

    return authenticator


def sync_user_from_authenticator():
    """
    streamlit-authenticator 인증 결과를 기존 CRM user 구조로 맞춥니다.
    """
    auth_status = st.session_state.get("authentication_status")
    username = st.session_state.get("username")

    if auth_status is True and username:
        user = get_user_by_username(username)

        if user:
            st.session_state.user = user
            return True

    st.session_state.user = None
    return False


def login_page(authenticator):
    hide_sidebar_before_login()

    st.title("사무실 CRM 로그인")

    try:
        authenticator.login(
            location="main",
            fields={
                "Form name": "로그인",
                "Username": "아이디",
                "Password": "비밀번호",
                "Login": "로그인"
            }
        )
    except TypeError:
        authenticator.login("로그인", "main")

    auth_status = st.session_state.get("authentication_status")

    if auth_status is False:
        st.error("아이디 또는 비밀번호가 틀렸습니다.")

    elif auth_status is None:
        st.info("아이디와 비밀번호를 입력하세요.")


def main():
    authenticator = make_authenticator()
    st.session_state.authenticator = authenticator

    is_logged_in = sync_user_from_authenticator()

    if is_logged_in:
        st.switch_page("pages/1_메인.py")
        return

    login_page(authenticator)

    is_logged_in = sync_user_from_authenticator()

    if is_logged_in:
        st.switch_page("pages/1_메인.py")


main()