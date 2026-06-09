import streamlit as st

from utils.page_common import require_login, render_sidebar
from views.customer_list import customer_list_page


st.set_page_config(
    page_title="고객 리스트",
    layout="wide"
)


def page():
    require_login()
    render_sidebar()

    user = st.session_state.user

    customer_list_page(user)


page()