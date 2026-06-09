import streamlit as st
import pandas as pd

from utils.auth import (
    create_user,
    get_users
)


def user_manage_page():

    st.subheader("직원 계정 생성")

    with st.form(
        "create_user_form"
    ):

        username = st.text_input(
            "로그인 아이디"
        )

        password = st.text_input(
            "비밀번호",
            type="password"
        )

        name = st.text_input(
            "직원 이름"
        )

        role = st.selectbox(
            "권한",
            [
                "staff",
                "admin"
            ]
        )

        submitted = (
            st.form_submit_button(
                "계정 생성"
            )
        )

        if submitted:

            if not username.strip():

                st.warning(
                    "아이디를 입력하세요."
                )

            elif not password.strip():

                st.warning(
                    "비밀번호를 입력하세요."
                )

            elif not name.strip():

                st.warning(
                    "직원 이름을 입력하세요."
                )

            else:

                try:

                    create_user(
                        username.strip(),
                        password.strip(),
                        name.strip(),
                        role
                    )

                    st.success(
                        "직원 계정이 생성되었습니다."
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"생성 실패: {e}"
                    )

    st.divider()

    st.subheader("직원 목록")

    users = get_users()

    if users:

        df = pd.DataFrame(users)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "등록된 직원이 없습니다."
        )