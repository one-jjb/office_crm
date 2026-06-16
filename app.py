import streamlit as st

from utils.auth import (
    verify_user,
    remember_login,
    restore_remembered_login,
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


def restore_user():
    if st.session_state.get("user") is not None:
        return True

    user = restore_remembered_login()

    if not user:
        return False

    st.session_state.user = user
    return True


def login_page():
    hide_sidebar_before_login()

    st.title("사무실 CRM 로그인")

    with st.form("login_form"):
        username = st.text_input("아이디")
        password = st.text_input("비밀번호", type="password")

        submitted = st.form_submit_button("로그인")

        if submitted:
            user = verify_user(username, password)

            if user:
                remember_login(user["id"])
                st.session_state.user = user
                st.switch_page("pages/1_메인.py")
            else:
                st.error("아이디 또는 비밀번호가 틀렸습니다.")


def main():
    if restore_user():
        st.switch_page("pages/1_메인.py")
        return

    login_page()


main()