import sqlite3

import pandas as pd
import streamlit as st

from utils.auth import (
    create_user,
    get_users,
)
from utils.page_common import render_view_header
from utils.ui import (
    render_card_start,
    render_card_end,
    render_section_title,
    render_metric_card,
)


def safe_value(value):
    return "" if value is None else str(value)


def user_manage_page():
    render_view_header(
        "직원 관리",
        "직원 계정을 생성하고 관리자 권한을 관리하세요.",
    )

    users = get_users()

    total_users = len(users)
    admin_users = len(
        [
            user
            for user in users
            if safe_value(user.get("role")) == "admin"
        ]
    )
    staff_users = len(
        [
            user
            for user in users
            if safe_value(user.get("role")) == "staff"
        ]
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        render_metric_card("전체 직원", total_users, "등록된 계정 수")

    with col2:
        render_metric_card("관리자", admin_users, "admin 권한")

    with col3:
        render_metric_card("직원", staff_users, "staff 권한")

    st.markdown("<br>", unsafe_allow_html=True)

    left, right = st.columns([0.88, 1.12])

    with left:
        render_card_start()
        render_section_title("직원 계정 생성")

        with st.form("create_user_form"):
            username = st.text_input(
                "로그인 아이디",
                placeholder="예: hong001",
            )

            password = st.text_input(
                "비밀번호",
                type="password",
                placeholder="초기 비밀번호 입력",
            )

            name = st.text_input(
                "직원 이름",
                placeholder="예: 홍길동",
            )

            role = st.selectbox(
                "권한",
                [
                    "staff",
                    "admin",
                ],
            )

            submitted = st.form_submit_button(
                "계정 생성",
                use_container_width=True,
            )

            if submitted:
                if not username.strip():
                    st.warning("아이디를 입력하세요.")
                elif not password.strip():
                    st.warning("비밀번호를 입력하세요.")
                elif not name.strip():
                    st.warning("직원 이름을 입력하세요.")
                else:
                    try:
                        create_user(
                            username.strip(),
                            password.strip(),
                            name.strip(),
                            role,
                        )

                        st.success("직원 계정이 생성되었습니다.")
                        st.rerun()

                    except sqlite3.IntegrityError:
                        st.error("이미 존재하는 아이디입니다.")

                    except Exception as e:
                        st.error(f"생성 실패: {e}")

        render_card_end()

    with right:
        render_card_start()
        render_section_title("직원 목록")

        if users:
            df = pd.DataFrame(users)

            preferred_columns = [
                "id",
                "username",
                "name",
                "role",
                "created_at",
            ]

            existing_columns = [
                column
                for column in preferred_columns
                if column in df.columns
            ]

            if existing_columns:
                df = df[existing_columns]

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
            )

        else:
            st.info("등록된 직원이 없습니다.")

        render_card_end()