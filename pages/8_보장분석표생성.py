# C:\office_crm\pages\8_보장분석표생성.py

import streamlit as st

from utils.page_common import require_login, render_sidebar
from views.coverage_workflow import coverage_workflow_page


st.set_page_config(
    page_title="보장분석표 생성",
    page_icon="📊",
    layout="wide",
)


def main():
    require_login()
    render_sidebar()

    user = st.session_state.get("user")

    if not user:
        st.warning("로그인이 필요합니다.")
        st.stop()

    coverage_workflow_page(user)


if __name__ == "__main__":
    main()