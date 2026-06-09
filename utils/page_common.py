import streamlit as st
from streamlit_local_storage import LocalStorage

localS = LocalStorage()


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


def require_login():
    if "user" not in st.session_state or st.session_state.user is None:
        st.warning("로그인이 필요합니다.")
        st.switch_page("app.py")


def require_admin():
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
    st.sidebar.page_link("pages/5_PDF변환.py", label="PDF 변환")
    st.sidebar.page_link("pages/6_엑셀분석.py", label="엑셀 분석")
    st.sidebar.page_link("pages/8_보장분석표생성.py", label="보장분석표 생성")

    if user["role"] == "admin":
        st.sidebar.divider()
        st.sidebar.page_link("pages/7_직원관리.py", label="직원 관리")
        st.sidebar.page_link("pages/9_매핑저장소관리.py", label="매핑 저장소 관리")

    st.sidebar.divider()

    if st.sidebar.button("로그아웃", width="stretch"):

        try:
            localS.deleteItem("crm_user")
        except:
            pass

        st.session_state.user = None
        st.switch_page("app.py")