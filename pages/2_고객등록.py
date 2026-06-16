import streamlit as st

from utils.page_common import require_login, init_page_ui, render_sidebar
from views.customer_register import customer_register_page


st.set_page_config(
    page_title="고객 등록",
    layout="wide",
)


def page():
    require_login()
    init_page_ui()
    render_sidebar()

    user = st.session_state.user

    customer_register_page(user)


page()