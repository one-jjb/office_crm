import streamlit as st

from utils.page_common import require_login, require_admin, render_sidebar
from views.user_manage import user_manage_page


st.set_page_config(
    page_title="직원 관리",
    layout="wide"
)


def page():
    require_login()
    require_admin()
    render_sidebar()

    user_manage_page()


page()