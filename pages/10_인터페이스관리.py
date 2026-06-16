import streamlit as st

from utils.page_common import (
    require_login,
    require_admin,
    init_page_ui,
    render_sidebar,
)
from views.interface_admin import interface_admin_page


st.set_page_config(
    page_title="인터페이스 관리",
    layout="wide",
)


def page():
    require_login()
    init_page_ui()
    render_sidebar()
    require_admin()

    user = st.session_state.user
    interface_admin_page(user)


page()