import streamlit as st

from utils.auth import (
    make_authenticator,
    sync_user_from_authenticator,
)


st.set_page_config(
    page_title="사무실 CRM",
    layout="wide"
)


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

    is_logged_in = sync_user_from_authenticator()

    if is_logged_in:
        st.switch_page("pages/1_메인.py")
        return

    login_page(authenticator)

    is_logged_in = sync_user_from_authenticator()

    if is_logged_in:
        st.switch_page("pages/1_메인.py")


main()