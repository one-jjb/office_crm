import streamlit as st

from utils.page_common import require_login, init_page_ui, render_sidebar
from views.consult_manage import consult_manage_page


st.set_page_config(
    page_title="상담 이력",
    layout="wide",
)


def page():
    require_login()
    init_page_ui()
    render_sidebar()

    user = st.session_state.user

    consult_manage_page(user)


page()