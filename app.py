import streamlit as st
import json

from streamlit_javascript import st_javascript
from utils.auth import verify_user

st.set_page_config(layout="wide")

# ----------------------------------
# sessionStorage 복원
# ----------------------------------

if "user" not in st.session_state:

    st.session_state.user = None

    try:

        saved_user = st_javascript(
            "sessionStorage.getItem('crm_user');"
        )

        if saved_user:

            st.session_state.user = json.loads(
                saved_user
            )

    except:
        pass

# ----------------------------------
# 로그인 상태
# ----------------------------------

st.write("SESSION")
st.write(st.session_state.get("user"))

try:

    st.write("BROWSER")

    st.write(
        st_javascript(
            "sessionStorage.getItem('crm_user');"
        )
    )

except Exception as e:

    st.write(e)

# ----------------------------------
# 로그인 완료
# ----------------------------------

if st.session_state.user:

    st.success(
        f"{st.session_state.user['name']} 로그인 유지중"
    )

    if st.button("로그아웃"):

        st_javascript(
            """
            sessionStorage.removeItem(
                'crm_user'
            );
            """
        )

        st.session_state.user = None

        st.rerun()

    st.stop()

# ----------------------------------
# 로그인 화면
# ----------------------------------

st.title("LOGIN TEST")

with st.form("login"):

    username = st.text_input("아이디")

    password = st.text_input(
        "비밀번호",
        type="password"
    )

    submit = st.form_submit_button(
        "로그인"
    )

    if submit:

        user = verify_user(
            username,
            password
        )

        if user:

            st.session_state.user = user

            st_javascript(
                f"""
                sessionStorage.setItem(
                    'crm_user',
                    '{json.dumps(user)}'
                );
                """
            )

            st.rerun()

        else:

            st.error(
                "로그인 실패"
            )