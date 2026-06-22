import html
import re
from datetime import date

import streamlit as st

from utils.customer import (
    get_customers,
    get_customer_by_id,
    update_customer,
    delete_customer,
)
from utils.page_common import render_view_header
from utils.ui import (
    render_card_start,
    render_card_end,
    render_section_title,
    get_status_class,
)


STATUS_OPTIONS = [
    "상담예정",
    "상담중",
    "분석중",
    "제안완료",
    "청약예정",
    "계약완료",
    "보류",
    "실패",
]

CUSTOMER_TYPE_OPTIONS = [
    "신규고객",
    "기존고객",
    "소개고객",
    "가망고객",
    "계약고객",
    "기타",
]

CARRIER_OPTIONS = [
    "",
    "SKT",
    "KT",
    "LG U+",
    "알뜰폰SK",
    "알뜰폰KT",
    "알뜰폰LG U+",
]

CUSTOMER_LIST_PANEL_HEIGHT = 720


def inject_customer_list_css():
    st.markdown(
        """
        <style>
        .customer-filter-summary {
            font-size: 13px;
            color: #94A3B8;
            margin-top: 6px;
        }

        .customer-list-scroll-note {
            font-size: 12px;
            color: #94A3B8;
            margin-top: 4px;
            margin-bottom: 12px;
        }

        @media screen and (max-width: 900px) {
            .customer-list-scroll-note {
                display: none;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def safe_value(value):
    return "" if value is None else str(value)


def safe_html(value, default="-"):
    text = safe_value(value).strip()

    if not text:
        text = default

    return html.escape(text)


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

    try:
        yy = int(birth6[:2])
        mm = int(birth6[2:4])
        dd = int(birth6[4:6])
    except Exception:
        return ""

    if gender_code in ["1", "2", "5", "6"]:
        year = 1900 + yy
    elif gender_code in ["3", "4", "7", "8"]:
        year = 2000 + yy
    elif gender_code in ["9", "0"]:
        year = 1800 + yy
    else:
        return ""

    try:
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


def _init_filter_state():
    st.session_state.setdefault("customer_list_search", "")
    st.session_state.setdefault("customer_list_status_filter", "전체")
    st.session_state.setdefault("customer_list_type_filter", "전체")


def _reset_filters():
    st.session_state.customer_list_search = ""
    st.session_state.customer_list_status_filter = "전체"
    st.session_state.customer_list_type_filter = "전체"


def _customer_matches_search(customer, keyword):
    keyword = safe_value(keyword).strip().lower()

    if not keyword:
        return True

    searchable_values = [
        customer.get("name"),
        customer.get("phone"),
        customer.get("carrier"),
        customer.get("rrn"),
        customer.get("address"),
        customer.get("memo"),
        customer.get("status"),
        customer.get("customer_type"),
        customer.get("owner_name"),
    ]

    joined = " ".join(
        safe_value(value).lower()
        for value in searchable_values
    )

    return keyword in joined


def _filter_customers(customers, keyword, status_filter, type_filter):
    filtered = []

    for customer in customers:
        status = safe_value(customer.get("status")).strip()
        customer_type = safe_value(customer.get("customer_type")).strip()

        if status_filter != "전체" and status != status_filter:
            continue

        if type_filter != "전체" and customer_type != type_filter:
            continue

        if not _customer_matches_search(customer, keyword):
            continue

        filtered.append(customer)

    return filtered


def render_customer_filters(customers):
    _init_filter_state()

    render_card_start()
    render_section_title("고객 필터")

    col_search, col_status, col_type, col_reset = st.columns(
        [0.38, 0.22, 0.22, 0.18]
    )

    with col_search:
        keyword = st.text_input(
            "검색",
            placeholder="고객명, 연락처, 주민번호, 주소, 메모 검색",
            key="customer_list_search",
        )

    with col_status:
        status_filter = st.selectbox(
            "진행상태",
            ["전체"] + STATUS_OPTIONS,
            key="customer_list_status_filter",
        )

    with col_type:
        type_filter = st.selectbox(
            "고객유형",
            ["전체"] + CUSTOMER_TYPE_OPTIONS,
            key="customer_list_type_filter",
        )

    with col_reset:
        st.markdown("<br>", unsafe_allow_html=True)

        st.button(
            "필터 초기화",
            use_container_width=True,
            key="customer_filter_reset_button",
            on_click=_reset_filters,
        )

    filtered_customers = _filter_customers(
        customers=customers,
        keyword=keyword,
        status_filter=status_filter,
        type_filter=type_filter,
    )

    st.markdown(
        f"""
        <div class="customer-filter-summary">
            전체 {len(customers)}명 중 {len(filtered_customers)}명이 표시됩니다.
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_card_end()

    return filtered_customers


def render_customer_card(customer, is_selected):
    customer_id = customer["id"]

    raw_name = safe_value(customer.get("name")).strip() or "이름없음"
    initial = safe_html(raw_name[:1], "?")

    name = safe_html(raw_name, "이름없음")
    phone = safe_html(
        format_phone_with_carrier(
            customer.get("phone"),
            customer.get("carrier"),
        ),
        "연락처 없음",
    )
    age = safe_html(get_age_from_rrn(customer.get("rrn")), "만 나이 없음")
    rrn = safe_html(format_mask_rrn(customer.get("rrn")), "-")
    address = safe_html(short_address(customer.get("address")), "-")
    status = safe_html(customer.get("status"), "상태 없음")
    customer_type = safe_html(customer.get("customer_type"), "유형 없음")

    selected_class = " customer-card-selected" if is_selected else ""
    badge_class = get_status_class(customer.get("status"))

    st.markdown(
        f"""
        <div class="crm-list-card{selected_class}">
            <div class="recent-customer-left">
                <div class="recent-avatar">{initial}</div>
                <div class="recent-main">
                    <div class="recent-name">
                        {name} <span class="crm-muted">({age})</span>
                    </div>
                    <div class="recent-meta">{customer_type} · {phone}</div>
                    <div class="recent-meta">주민번호 {rrn} · {address}</div>
                </div>
            </div>
            <div class="recent-customer-right">
                <div class="recent-status {badge_class}">{status}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_select, col_consult = st.columns([0.5, 0.5])

    with col_select:
        button_label = "선택됨" if is_selected else "상세 / 수정"

        if st.button(
            button_label,
            key=f"select_customer_{customer_id}",
            use_container_width=True,
        ):
            st.session_state.selected_customer_id = customer_id
            st.rerun()

    with col_consult:
        if st.button(
            "상담",
            key=f"go_consult_{customer_id}",
            use_container_width=True,
        ):
            st.session_state.selected_consult_customer_id = customer_id
            st.switch_page("pages/4_상담이력.py")


def render_customer_detail_form(customer, selected_customer_id, user):
    render_card_start()
    render_section_title("고객 상세 / 수정")

    age_text = get_age_from_rrn(customer.get("rrn")) or "만 나이 계산 불가"

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
                index=type_index,
            )

            name = st.text_input(
                "고객명",
                value=safe_value(customer.get("name")),
            )

            phone_col, carrier_col = st.columns([2, 1])

            with phone_col:
                phone = st.text_input(
                    "연락처",
                    value=safe_value(customer.get("phone")),
                    placeholder="예: 01012345678",
                )

            with carrier_col:
                carrier = st.selectbox(
                    "통신사",
                    CARRIER_OPTIONS,
                    index=carrier_index,
                )

        with col2:
            rrn_col, age_col = st.columns([1.4, 0.8])

            with rrn_col:
                rrn = st.text_input(
                    "주민번호",
                    value=safe_value(customer.get("rrn")),
                )

            with age_col:
                st.text_input(
                    "만 나이",
                    value=age_text,
                    disabled=True,
                )

            status = st.selectbox(
                "진행상태",
                STATUS_OPTIONS,
                index=status_index,
            )

            owner_name = safe_value(customer.get("owner_name"))
            created_at = safe_value(customer.get("created_at"))

            st.text_input("담당자", value=owner_name, disabled=True)
            st.text_input("등록일", value=created_at, disabled=True)

        address = st.text_area(
            "주소",
            value=safe_value(customer.get("address")),
            height=90,
        )

        memo = st.text_area(
            "메모",
            value=safe_value(customer.get("memo")),
            height=120,
        )

        col_save, col_consult = st.columns(2)

        with col_save:
            submitted = st.form_submit_button(
                "저장",
                use_container_width=True,
            )

        with col_consult:
            go_consult = st.form_submit_button(
                "상담 이력으로 이동",
                use_container_width=True,
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
                    memo=memo.strip(),
                )

                st.success("고객 정보가 저장되었습니다.")
                st.rerun()

        if go_consult:
            st.session_state.selected_consult_customer_id = selected_customer_id
            st.switch_page("pages/4_상담이력.py")

    render_card_end()

    render_card_start()
    render_section_title("고객 삭제")

    st.warning("고객을 삭제하면 해당 고객의 상담 이력도 함께 삭제됩니다.")

    confirm_text = st.text_input(
        "삭제하려면 고객명을 그대로 입력하세요.",
        key=f"delete_confirm_{selected_customer_id}",
    )

    if st.button(
        "고객 삭제",
        key=f"delete_customer_{selected_customer_id}",
        use_container_width=True,
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

    render_card_end()


def render_customer_list_area(filtered_customers):
    render_card_start()
    render_section_title("고객 목록")

    st.caption(
        "진행상태와 고객유형으로 필터링하고, 고객 카드를 선택하면 오른쪽에서 상세 수정이 가능합니다."
    )

    st.markdown(
        """
        <div class="customer-list-scroll-note">
            고객 목록이 많을 경우 이 영역 안에서만 스크롤됩니다.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(
        height=CUSTOMER_LIST_PANEL_HEIGHT,
        border=False,
    ):
        if not filtered_customers:
            st.info("필터 조건에 맞는 고객이 없습니다.")
        else:
            for customer in filtered_customers:
                is_selected = (
                    st.session_state.selected_customer_id == customer["id"]
                )
                render_customer_card(customer, is_selected)

    render_card_end()


def render_customer_detail_area(user, selected_customer_id):
    if not selected_customer_id:
        render_card_start()
        render_section_title("상세 정보")
        st.info("상세보기 또는 수정을 하려면 고객을 선택하세요.")
        render_card_end()
        return

    customer = get_customer_by_id(selected_customer_id)

    if not customer:
        render_card_start()
        render_section_title("상세 정보")
        st.warning("고객 정보를 찾을 수 없습니다.")
        render_card_end()
        return

    render_customer_detail_form(customer, selected_customer_id, user)


def customer_list_page(user):
    inject_customer_list_css()

    render_view_header(
        "고객 리스트",
        "등록된 고객을 필터로 정리하고 상세 정보, 상담 이력, 진행 상태를 관리하세요.",
    )

    customers = get_customers(user)

    if not customers:
        st.info("등록된 고객이 없습니다.")
        return

    if "selected_customer_id" not in st.session_state:
        st.session_state.selected_customer_id = None

    all_customer_ids = [customer["id"] for customer in customers]

    if st.session_state.selected_customer_id not in all_customer_ids:
        st.session_state.selected_customer_id = None

    filtered_customers = render_customer_filters(customers)
    filtered_customer_ids = [customer["id"] for customer in filtered_customers]

    if (
        st.session_state.selected_customer_id
        and st.session_state.selected_customer_id not in filtered_customer_ids
    ):
        st.session_state.selected_customer_id = None

    st.markdown("<br>", unsafe_allow_html=True)

    left, right = st.columns([1.12, 0.88])

    with left:
        render_customer_list_area(filtered_customers)

    with right:
        render_customer_detail_area(
            user=user,
            selected_customer_id=st.session_state.selected_customer_id,
        )