import html

import streamlit as st

from utils.auth import restore_remembered_login, clear_remembered_login
from utils.ui import get_current_theme, inject_global_css, render_theme_toggle


def restore_user():
    if st.session_state.get("user"):
        return True

    user = restore_remembered_login()

    if user:
        st.session_state.user = user
        return True

    return False


def require_login():
    if restore_user():
        return

    st.switch_page("app.py")


def require_admin():
    user = st.session_state.get("user")

    if not user:
        st.switch_page("app.py")
        return

    if user.get("role") != "admin":
        st.error("관리자만 접근할 수 있습니다.")
        st.stop()


def init_page_ui():
    theme_mode = get_current_theme()
    inject_global_css(theme_mode)

    return theme_mode


def render_sidebar():
    user = st.session_state.get("user", {})
    user_name = html.escape(str(user.get("name", "사용자")))
    user_role = html.escape(str(user.get("role", "user")))

    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-profile-card">
                <div class="sidebar-profile-title">Office CRM</div>
                <div class="sidebar-profile-name">{user_name}</div>
                <div class="sidebar-profile-role">{user_role}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            """
            <div class="sidebar-section-title">메뉴</div>
            """,
            unsafe_allow_html=True,
        )

        st.page_link(
            "pages/1_메인.py",
            label="메인",
            icon="🏠",
        )

        st.page_link(
            "pages/2_고객등록.py",
            label="고객 등록",
            icon="➕",
        )

        st.page_link(
            "pages/3_고객리스트.py",
            label="고객 리스트",
            icon="👥",
        )

        st.page_link(
            "pages/4_상담이력.py",
            label="상담 이력",
            icon="📝",
        )

        if user.get("role") == "admin":
            st.markdown("---")

            st.markdown(
                """
                <div class="sidebar-section-title">관리자 메뉴</div>
                """,
                unsafe_allow_html=True,
            )

            st.page_link(
                "pages/7_직원관리.py",
                label="직원 관리",
                icon="⚙️",
            )

            st.page_link(
                "pages/10_인터페이스관리.py",
                label="인터페이스 관리",
                icon="🎨",
            )

        st.markdown("---")

        st.markdown(
            """
            <div class="sidebar-section-title">화면 설정</div>
            """,
            unsafe_allow_html=True,
        )

        render_theme_toggle(key="sidebar_theme_toggle")

        st.markdown("---")

        if st.button(
            "로그아웃",
            use_container_width=True,
            key="sidebar_logout_button",
        ):
            clear_remembered_login()
            st.session_state.user = None
            st.switch_page("app.py")


def render_view_header(title, subtitle=None):
    from utils.ui import render_page_header

    top_left, top_right = st.columns([0.82, 0.18])

    with top_left:
        render_page_header(title, subtitle)

    with top_right:
        render_theme_toggle(key=f"theme_toggle_{title}")