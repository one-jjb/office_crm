import re
import streamlit as st

from utils.customer import (
    get_customers,
    get_customer_by_id,
    update_customer,
    delete_customer
)

STATUS_OPTIONS = [
    "상담예정", "상담중", "분석중", "제안완료",
    "청약예정", "계약완료", "보류", "실패"
]

CUSTOMER_TYPE_OPTIONS = [
    "신규고객", "기존고객", "소개고객",
    "가망고객", "계약고객", "기타"
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


def safe_value(value):
    return "" if value is None else str(value)


def only_digits(value):
    return re.sub(r"\D", "", safe_value(value))


def format_phone(phone):
    digits = only_digits(phone)

    if len(digits) == 11:
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"

    if len(digits) == 10:
        if digits.startswith("02"):
            return f"{digits[:2]}-{digits[2:6]}-{digits[6:]}"
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"

    if len(digits) == 9 and digits.startswith("02"):
        return f"{digits[:2]}-{digits[2:5]}-{digits[5:]}"

    return safe_value(phone)


def format_phone_with_carrier(phone, carrier):
    phone_text = format_phone(phone)
    carrier_text = safe_value(carrier).strip()

    if phone_text and carrier_text:
        return f"{phone_text} / {carrier_text}"

    if phone_text:
        return phone_text

    if carrier_text:
        return carrier_text

    return ""


def format_mask_rrn(rrn):
    digits = only_digits(rrn)

    if len(digits) >= 13:
        return f"{digits[:6]}-{digits[6]}******"

    if len(digits) >= 7:
        return f"{digits[:6]}-{digits[6]}{'*' * (len(digits) - 7)}"

    if len(digits) == 6:
        return f"{digits}-"

    return safe_value(rrn)


def get_age_from_rrn(rrn):
    digits = only_digits(rrn)

    if len(digits) < 7:
        return ""

    birth6 = digits[:6]
    gender_code = digits[6]

    yy = int(birth6[:2])
    mm = int(birth6[2:4])
    dd = int(birth6[4:6])

    if gender_code in ["1", "2", "5", "6"]:
        year = 1900 + yy
    elif gender_code in ["3", "4", "7", "8"]:
        year = 2000 + yy
    else:
        return ""

    try:
        from datetime import date

        today = date.today()
        birthday = date(year, mm, dd)

        age = today.year - birthday.year

        if (today.month, today.day) < (birthday.month, birthday.day):
            age -= 1

        return f"만 {age}세"

    except ValueError:
        return ""


def short_address(address):
    text = safe_value(address).strip()

    if not text:
        return ""

    parts = text.split()

    if len(parts) >= 2:
        return f"{parts[0]} {parts[1]}"

    return text


def customer_list_page(user):
    st.subheader("고객 리스트")

    customers = get_customers(user)

    if not customers:
        st.info("등록된 고객이 없습니다.")
        return

    if "selected_customer_id" not in st.session_state:
        st.session_state.selected_customer_id = None

    customer_ids = [customer["id"] for customer in customers]

    if st.session_state.selected_customer_id not in customer_ids:
        st.session_state.selected_customer_id = None

    st.caption("고객명을 누르면 아래에 상세/수정 화면이 열립니다.")

    with st.container(border=True):
        header_cols = st.columns([1.6, 1.1, 2, 2.2, 2, 1])

        with header_cols[0]:
            st.markdown("**이름**")

        with header_cols[1]:
            st.markdown("**만 나이**")

        with header_cols[2]:
            st.markdown("**주민번호**")

        with header_cols[3]:
            st.markdown("**연락처 / 통신사**")

        with header_cols[4]:
            st.markdown("**주소**")

        with header_cols[5]:
            st.markdown("**상담**")

        st.divider()

        for customer in customers:
            is_selected = (
                st.session_state.selected_customer_id == customer["id"]
            )

            row_cols = st.columns([1.6, 1.1, 2, 2.2, 2, 1])

            with row_cols[0]:
                button_label = customer.get("name") or "이름없음"

                if is_selected:
                    button_label = f"✅ {button_label}"

                if st.button(
                    button_label,
                    key=f"select_customer_{customer['id']}",
                    use_container_width=True
                ):
                    st.session_state.selected_customer_id = customer["id"]
                    st.rerun()

            with row_cols[1]:
                st.write(get_age_from_rrn(customer.get("rrn")))

            with row_cols[2]:
                st.write(format_mask_rrn(customer.get("rrn")))

            with row_cols[3]:
                st.write(
                    format_phone_with_carrier(
                        customer.get("phone"),
                        customer.get("carrier")
                    )
                )

            with row_cols[4]:
                st.write(short_address(customer.get("address")))

            with row_cols[5]:
                if st.button(
                    "상담",
                    key=f"go_consult_{customer['id']}",
                    use_container_width=True
                ):
                    st.session_state.selected_consult_customer_id = customer["id"]
                    st.switch_page("pages/4_상담이력.py")

    st.divider()

    selected_customer_id = st.session_state.selected_customer_id

    if not selected_customer_id:
        st.info("상세보기 또는 수정을 하려면 고객명을 선택하세요.")
        return

    customer = get_customer_by_id(selected_customer_id)

    if not customer:
        st.warning("고객 정보를 찾을 수 없습니다.")
        return

    st.subheader("고객 상세 / 수정")

    with st.form(f"customer_detail_edit_form_{selected_customer_id}"):

        col1, col2 = st.columns(2)

        current_type = customer.get("customer_type") or CUSTOMER_TYPE_OPTIONS[0]
        current_status = customer.get("status") or STATUS_OPTIONS[0]
        current_carrier = customer.get("carrier") or ""

        type_index = (
            CUSTOMER_TYPE_OPTIONS.index(current_type)
            if current_type in CUSTOMER_TYPE_OPTIONS
            else 0
        )

        status_index = (
            STATUS_OPTIONS.index(current_status)
            if current_status in STATUS_OPTIONS
            else 0
        )

        carrier_index = (
            CARRIER_OPTIONS.index(current_carrier)
            if current_carrier in CARRIER_OPTIONS
            else 0
        )

        with col1:
            customer_type = st.selectbox(
                "고객유형",
                CUSTOMER_TYPE_OPTIONS,
                index=type_index
            )

            name = st.text_input(
                "고객명",
                value=safe_value(customer.get("name"))
            )

            phone_col, carrier_col = st.columns([2, 1])

            with phone_col:
                phone = st.text_input(
                    "연락처",
                    value=safe_value(customer.get("phone")),
                    placeholder="예: 01012345678"
                )

            with carrier_col:
                carrier = st.selectbox(
                    "통신사",
                    CARRIER_OPTIONS,
                    index=carrier_index
                )

        with col2:
            rrn = st.text_input(
                "주민번호",
                value=safe_value(customer.get("rrn"))
            )

            status = st.selectbox(
                "진행상태",
                STATUS_OPTIONS,
                index=status_index
            )

            owner_name = safe_value(customer.get("owner_name"))
            created_at = safe_value(customer.get("created_at"))

            st.text_input("담당자", value=owner_name, disabled=True)
            st.text_input("등록일", value=created_at, disabled=True)

        address = st.text_area(
            "주소",
            value=safe_value(customer.get("address")),
            height=90
        )

        memo = st.text_area(
            "메모",
            value=safe_value(customer.get("memo")),
            height=120
        )

        col_save, col_consult = st.columns(2)

        with col_save:
            submitted = st.form_submit_button(
                "저장",
                use_container_width=True
            )

        with col_consult:
            go_consult = st.form_submit_button(
                "상담 이력으로 이동",
                use_container_width=True
            )

        if submitted:
            if not name.strip():
                st.warning("고객명을 입력하세요.")
            else:
                update_customer(
                    customer_id=selected_customer_id,
                    customer_type=customer_type,
                    name=name.strip(),
                    phone=phone.strip(),
                    carrier=carrier.strip(),
                    rrn=rrn.strip(),
                    address=address.strip(),
                    status=status,
                    memo=memo.strip()
                )

                st.success("고객 정보가 저장되었습니다.")
                st.rerun()

        if go_consult:
            st.session_state.selected_consult_customer_id = selected_customer_id
            st.switch_page("pages/4_상담이력.py")

    st.divider()

    with st.expander("고객 삭제"):
        st.warning("고객을 삭제하면 해당 고객의 상담 이력도 함께 삭제됩니다.")

        confirm_text = st.text_input(
            "삭제하려면 고객명을 그대로 입력하세요.",
            key=f"delete_confirm_{selected_customer_id}"
        )

        if st.button(
            "고객 삭제",
            key=f"delete_customer_{selected_customer_id}",
            use_container_width=True
        ):
            if confirm_text.strip() != safe_value(customer.get("name")).strip():
                st.error("고객명이 일치하지 않아 삭제하지 않았습니다.")
            else:
                deleted = delete_customer(selected_customer_id, user)

                if deleted:
                    st.success("고객이 삭제되었습니다.")
                    st.session_state.selected_customer_id = None
                    st.rerun()
                else:
                    st.error("삭제 권한이 없거나 고객을 찾을 수 없습니다.")