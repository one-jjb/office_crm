import streamlit as st

from utils.page_common import require_login, render_sidebar
from views.excel_analyze import excel_analyze_page


st.set_page_config(
    page_title="엑셀 분석",
    layout="wide"
)


def page():
    require_login()
    render_sidebar()

    user = st.session_state.user

    excel_analyze_page(user)


page()