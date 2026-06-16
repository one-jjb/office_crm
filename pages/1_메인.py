import streamlit as st

from utils.page_common import require_login, init_page_ui, render_sidebar
from views.home import home_page


st.set_page_config(
    page_title="메인",
    layout="wide",
)


def page():
    require_login()
    init_page_ui()
    render_sidebar()

    user = st.session_state.user

    home_page(user)


page()