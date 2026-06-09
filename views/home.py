import streamlit as st

from utils.ui import inject_global_css
from utils.customer import get_customers


def home_page(user):

    # ======================================================
    # 글로벌 UI
    # ======================================================

    inject_global_css()

    # ======================================================
    # 고객 데이터
    # ======================================================

    customers = get_customers(user)

    total_customers = len(customers)

    recent_customers = customers[-5:] if customers else []

    # ======================================================
    # 헤더
    # ======================================================

    st.title("Dashboard")

    st.caption(
        f"안녕하세요, {user.get('name', '사용자')}님 👋"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ======================================================
    # KPI
    # ======================================================

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            label="전체 고객",
            value=total_customers
        )

    with col2:

        st.metric(
            label="오늘 상담",
            value="-"
        )

    with col3:

        st.metric(
            label="보장 분석",
            value="-"
        )

    with col4:

        st.metric(
            label="진행 계약",
            value="-"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ======================================================
    # 메인 레이아웃
    # ======================================================

    left, right = st.columns([1.5, 0.9])

    # ======================================================
    # 최근 고객
    # ======================================================

    with left:

        st.subheader("최근 고객")

        if recent_customers:

            table_data = []

            for customer in reversed(recent_customers):

                table_data.append({
                    "고객명": customer.get("name", ""),
                    "연락처": customer.get("phone", ""),
                    "생년월일": customer.get("birth", "")
                })

            st.dataframe(
                table_data,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info("등록된 고객이 없습니다.")

    # ======================================================
    # 빠른 메뉴
    # ======================================================

    with right:

        st.subheader("빠른 메뉴")

        if st.button(
            "고객 등록",
            use_container_width=True
        ):
            st.switch_page("pages/2_고객등록.py")

        if st.button(
            "고객 리스트",
            use_container_width=True
        ):
            st.switch_page("pages/3_고객리스트.py")

        if st.button(
            "상담 이력",
            use_container_width=True
        ):
            st.switch_page("pages/4_상담이력.py")

        if st.button(
            "PDF 변환",
            use_container_width=True
        ):
            st.switch_page("pages/5_PDF변환.py")

        if st.button(
            "보장분석표 생성",
            use_container_width=True
        ):
            st.switch_page("pages/8_보장분석표생성.py")