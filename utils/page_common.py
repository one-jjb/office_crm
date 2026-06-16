import streamlit as st

from utils.auth import (
    get_user_by_session_token,
    delete_login_session,
)


def hide_default_streamlit_nav():
    st.markdown(
        """
        <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_sid_from_query():
    sid = st.query_params.get("sid")

    if isinstance(sid, list):
        return sid[0] if sid else None

    return sid


def restore_user_from_sid():
    if st.session_state.get("user") is not None:
        return True

    sid = st.session_state.get("session_token") or get_sid_from_query()

    if not sid:
        return False

    user = get_user_by_session_token(sid)

    if not user:
        return False

    st.session_state.user = user
    st.session_state.session_token = sid

    try:
        st.query_params["sid"] = sid
    except Exception:
        pass

    return True


def require_login():
    is_logged_in = restore_user_from_sid()

    if not is_logged_in:
        st.warning("로그인이 필요합니다.")
        st.switch_page("app.py")


def require_admin():
    require_login()

    user = st.session_state.user

    if user["role"] != "admin":
        st.error("관리자만 접근할 수 있습니다.")
        st.stop()


def render_sidebar():
    hide_default_streamlit_nav()

    user = st.session_state.user

    st.sidebar.success(f"{user['name']}님")
    st.sidebar.write(f"권한: {user['role']}")

    st.sidebar.divider()

    st.sidebar.page_link("pages/1_메인.py", label="메인")
    st.sidebar.page_link("pages/2_고객등록.py", label="고객 등록")
    st.sidebar.page_link("pages/3_고객리스트.py", label="고객 리스트")
    st.sidebar.page_link("pages/4_상담이력.py", label="상담 이력")

    if user["role"] == "admin":
        st.sidebar.divider()
        st.sidebar.page_link("pages/7_직원관리.py", label="직원 관리")

    st.sidebar.divider()

    if st.sidebar.button("로그아웃", width="stretch"):
        sid = st.session_state.get("session_token") or get_sid_from_query()

        if sid:
            delete_login_session(sid)

        st.session_state.user = None
        st.session_state.session_token = None

        try:
            del st.query_params["sid"]
        except Exception:
            pass

        st.switch_page("app.py")