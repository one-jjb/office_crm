import streamlit as st

from utils.customer import add_customer

STATUS_OPTIONS = [
    "상담예정",
    "상담중",
    "분석중",
    "제안완료",
    "청약예정",
    "계약완료",
    "보류",
    "실패"
]

CUSTOMER_TYPE_OPTIONS = [
    "신규고객",
    "기존고객",
    "소개고객",
    "가망고객",
    "계약고객",
    "기타"
]

CARRIER_OPTIONS = [
    "",
    "SKT",
    "KT",
    "LG U+",
    "알뜰폰SK",
    "알뜰폰KT",
    "알뜰폰LG U+"
]


def customer_register_page(user):

    st.subheader("고객 등록")

    if "customer_register_nonce" not in st.session_state:
        st.session_state.customer_register_nonce = 0

    if "customer_register_success" not in st.session_state:
        st.session_state.customer_register_success = False

    if st.session_state.customer_register_success:
        st.success("고객 등록이 완료되었습니다.")
        st.session_state.customer_register_success = False

    form_nonce = st.session_state.customer_register_nonce

    with st.form(f"customer_form_{form_nonce}"):

        col1, col2 = st.columns(2)

        with col1:
            customer_type = st.selectbox(
                "고객유형",
                CUSTOMER_TYPE_OPTIONS,
                key=f"customer_type_{form_nonce}"
            )

            name = st.text_input(
                "고객명",
                key=f"name_{form_nonce}"
            )

            phone_col, carrier_col = st.columns([2, 1])

            with phone_col:
                phone = st.text_input(
                    "연락처",
                    placeholder="예: 01012345678",
                    key=f"phone_{form_nonce}"
                )

            with carrier_col:
                carrier = st.selectbox(
                    "통신사",
                    CARRIER_OPTIONS,
                    key=f"carrier_{form_nonce}"
                )

        with col2:
            rrn = st.text_input(
                "주민번호",
                placeholder="예: 900101-1******",
                key=f"rrn_{form_nonce}"
            )

            address = st.text_area(
                "주소",
                height=100,
                key=f"address_{form_nonce}"
            )

            status = st.selectbox(
                "진행상태",
                STATUS_OPTIONS,
                key=f"status_{form_nonce}"
            )

        memo = st.text_area(
            "메모",
            key=f"memo_{form_nonce}"
        )

        submitted = st.form_submit_button("고객 저장")

        if submitted:
            if not name.strip():
                st.warning("고객명을 입력하세요.")
            else:
                add_customer(
                    owner_user_id=user["id"],
                    customer_type=customer_type,
                    name=name.strip(),
                    phone=phone.strip(),
                    carrier=carrier.strip(),
                    rrn=rrn.strip(),
                    address=address.strip(),
                    status=status,
                    memo=memo.strip()
                )

                st.session_state.customer_register_nonce += 1
                st.session_state.customer_register_success = True

                st.rerun()