import streamlit as st

from utils.page_common import require_login, render_sidebar
from views.claim_analyze import claim_analyze_page


st.set_page_config(
    page_title="PDF 변환",
    layout="wide"
)


def page():
    require_login()
    render_sidebar()

    user = st.session_state.user

    claim_analyze_page(user)


page()