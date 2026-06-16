import streamlit as st

from utils.auth import (
    verify_user,
    create_login_session,
    get_user_by_session_token,
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


def get_sid_from_query():
    sid = st.query_params.get("sid")

    if isinstance(sid, list):
        return sid[0] if sid else None

    return sid


def restore_user_from_sid():
    if st.session_state.get("user") is not None:
        return True

    sid = get_sid_from_query()

    if not sid:
        return False

    user = get_user_by_session_token(sid)

    if not user:
        return False

    st.session_state.user = user
    st.session_state.session_token = sid

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
                token = create_login_session(user["id"])

                st.session_state.user = user
                st.session_state.session_token = token

                st.query_params["sid"] = token

                st.switch_page("pages/1_메인.py")
            else:
                st.error("아이디 또는 비밀번호가 틀렸습니다.")


def main():
    is_logged_in = restore_user_from_sid()

    if is_logged_in:
        st.switch_page("pages/1_메인.py")
        return

    login_page()


main()