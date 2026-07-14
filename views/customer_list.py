import html
import re
from datetime import date

import streamlit as st

from utils.consult import get_consult_logs
from utils.customer import (
    get_customers,
    get_customer_by_id,
    update_customer,
    delete_customer,
)
from utils.ui import (
    render_page_header,
    render_section_title,
)


STATUS_OPTIONS = [
    "콜 대기",
    "콜 부재",
    "콜 거절",
    "상담 예정",
    "상담 중",
    "설계 중",
    "증권 전달",
    "계약 완료",
    "거절",
    "기타",
]

CUSTOMER_TYPE_OPTIONS = [
    "DB고객",
    "소개고객",
    "방문고객",
    "기고객",
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
            color: #CBD5E1;
            margin-top: 6px;
        }

        .customer-list-scroll-note {
            font-size: 12px;
            color: #CBD5E1;
            margin-top: 4px;
            margin-bottom: 12px;
        }

        .customer-consult-divider {
            height: 1px;
            margin: 24px 0 20px 0;
            background: rgba(148, 163, 184, 0.25);
        }

        .customer-consult-count {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 28px;
            height: 24px;
            padding: 0 8px;
            margin-left: 8px;
            border-radius: 999px;
            color: #BFDBFE;
            background: rgba(59, 130, 246, 0.18);
            border: 1px solid rgba(96, 165, 250, 0.30);
            font-size: 12px;
            font-weight: 800;
        }

        .customer-consult-heading {
            display: flex;
            align-items: center;
            margin-bottom: 13px;
            color: #F8FAFC;
            font-size: 20px;
            font-weight: 800;
            letter-spacing: -0.04em;
        }

        .customer-consult-meta {
            margin-top: 8px;
            color: #94A3B8;
            font-size: 12px;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(15, 23, 42, 0.78) !important;
            border: 1px solid rgba(148, 163, 184, 0.24) !important;
            border-radius: 22px !important;
            box-shadow: 0 18px 50px rgba(0, 0, 0, 0.20) !important;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] * {
            color: #E5E7EB;
        }

        div[data-testid="stForm"] {
            background: rgba(15, 23, 42, 0.82) !important;
            border: 1px solid rgba(148, 163, 184, 0.24) !important;
            border-radius: 22px !important;
            box-shadow: none !important;
        }

        div[data-testid="stForm"] label,
        div[data-testid="stForm"] p,
        div[data-testid="stForm"] span {
            color: #E5E7EB !important;
        }

        .crm-section-title {
            color: #F8FAFC !important;
        }

        .crm-muted {
            color: #CBD5E1 !important;
        }

        div[class*="st-key-customer_card_status_"],
        div[class*="st-key-selected_customer_card_status_"] {
            margin-bottom: 8px;
        }

        div[class*="st-key-customer_card_status_"] button,
        div[class*="st-key-selected_customer_card_status_"] button {
            position: relative !important;
            display: flex !important;
            width: 100% !important;
            height: auto !important;
            min-height: 72px !important;
            justify-content: flex-start !important;
            align-items: center !important;
            text-align: left !important;
            padding: 10px 108px 10px 14px !important;
            border-radius: 15px !important;
            background: rgba(30, 41, 59, 0.94) !important;
            border: 1px solid rgba(148, 163, 184, 0.22) !important;
            border-left-width: 5px !important;
            box-shadow: none !important;
            color: #F8FAFC !important;
            transition: 0.15s ease !important;
            overflow: hidden !important;
        }

        div[class*="st-key-customer_card_status_"] button:hover,
        div[class*="st-key-selected_customer_card_status_"] button:hover {
            background: rgba(51, 65, 85, 0.98) !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 8px 22px rgba(0, 0, 0, 0.18) !important;
        }

        div[class*="st-key-selected_customer_card_status_"] button {
            background: rgba(30, 64, 175, 0.46) !important;
            box-shadow: 0 0 0 2px rgba(96, 165, 250, 0.48) !important;
            filter: brightness(1.08);
        }

        div[class*="st-key-customer_card_status_"] button p,
        div[class*="st-key-selected_customer_card_status_"] button p {
            width: 100% !important;
            max-width: 100% !important;
            color: #CBD5E1 !important;
            white-space: pre-line !important;
            line-height: 1.38 !important;
            font-size: 12.5px !important;
            font-weight: 620 !important;
            text-align: left !important;
            margin: 0 !important;
            letter-spacing: -0.02em !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
        }

        div[class*="st-key-customer_card_status_"] button p strong,
        div[class*="st-key-selected_customer_card_status_"] button p strong {
            color: #FFFFFF !important;
            font-size: 15px !important;
            font-weight: 850 !important;
            letter-spacing: -0.04em !important;
        }

        div[class*="st-key-customer_card_status_"] button::after,
        div[class*="st-key-selected_customer_card_status_"] button::after {
            position: absolute;
            top: 50%;
            right: 12px;
            transform: translateY(-50%);
            min-width: 72px;
            padding: 5px 8px;
            border-radius: 999px;
            text-align: center;
            font-size: 11px;
            line-height: 1.2;
            font-weight: 850;
            letter-spacing: -0.03em;
            border: 1px solid transparent;
            box-sizing: border-box;
        }

        div[class*="st-key-customer_card_status_call_wait_"] button,
        div[class*="st-key-selected_customer_card_status_call_wait_"] button {
            border-left-color: #A78BFA !important;
        }

        div[class*="st-key-customer_card_status_call_wait_"] button::after,
        div[class*="st-key-selected_customer_card_status_call_wait_"] button::after {
            content: "콜 대기";
            color: #DDD6FE;
            background: rgba(139, 92, 246, 0.20);
            border-color: rgba(167, 139, 250, 0.40);
        }

        div[class*="st-key-customer_card_status_call_absent_"] button,
        div[class*="st-key-selected_customer_card_status_call_absent_"] button {
            border-left-color: #FBBF24 !important;
        }

        div[class*="st-key-customer_card_status_call_absent_"] button::after,
        div[class*="st-key-selected_customer_card_status_call_absent_"] button::after {
            content: "콜 부재";
            color: #FDE68A;
            background: rgba(245, 158, 11, 0.20);
            border-color: rgba(251, 191, 36, 0.40);
        }

        div[class*="st-key-customer_card_status_call_reject_"] button,
        div[class*="st-key-selected_customer_card_status_call_reject_"] button {
            border-left-color: #FB7185 !important;
        }

        div[class*="st-key-customer_card_status_call_reject_"] button::after,
        div[class*="st-key-selected_customer_card_status_call_reject_"] button::after {
            content: "콜 거절";
            color: #FECDD3;
            background: rgba(244, 63, 94, 0.20);
            border-color: rgba(251, 113, 133, 0.42);
        }

        div[class*="st-key-customer_card_status_consult_scheduled_"] button,
        div[class*="st-key-selected_customer_card_status_consult_scheduled_"] button {
            border-left-color: #C084FC !important;
        }

        div[class*="st-key-customer_card_status_consult_scheduled_"] button::after,
        div[class*="st-key-selected_customer_card_status_consult_scheduled_"] button::after {
            content: "상담 예정";
            color: #E9D5FF;
            background: rgba(168, 85, 247, 0.20);
            border-color: rgba(192, 132, 252, 0.42);
        }

        div[class*="st-key-customer_card_status_consult_active_"] button,
        div[class*="st-key-selected_customer_card_status_consult_active_"] button {
            border-left-color: #60A5FA !important;
        }

        div[class*="st-key-customer_card_status_consult_active_"] button::after,
        div[class*="st-key-selected_customer_card_status_consult_active_"] button::after {
            content: "상담 중";
            color: #BFDBFE;
            background: rgba(59, 130, 246, 0.20);
            border-color: rgba(96, 165, 250, 0.42);
        }

        div[class*="st-key-customer_card_status_design_active_"] button,
        div[class*="st-key-selected_customer_card_status_design_active_"] button {
            border-left-color: #22D3EE !important;
        }

        div[class*="st-key-customer_card_status_design_active_"] button::after,
        div[class*="st-key-selected_customer_card_status_design_active_"] button::after {
            content: "설계 중";
            color: #CFFAFE;
            background: rgba(6, 182, 212, 0.20);
            border-color: rgba(34, 211, 238, 0.42);
        }

        div[class*="st-key-customer_card_status_policy_delivered_"] button,
        div[class*="st-key-selected_customer_card_status_policy_delivered_"] button {
            border-left-color: #2DD4BF !important;
        }

        div[class*="st-key-customer_card_status_policy_delivered_"] button::after,
        div[class*="st-key-selected_customer_card_status_policy_delivered_"] button::after {
            content: "증권 전달";
            color: #CCFBF1;
            background: rgba(20, 184, 166, 0.20);
            border-color: rgba(45, 212, 191, 0.42);
        }

        div[class*="st-key-customer_card_status_contract_done_"] button,
        div[class*="st-key-selected_customer_card_status_contract_done_"] button {
            border-left-color: #4ADE80 !important;
        }

        div[class*="st-key-customer_card_status_contract_done_"] button::after,
        div[class*="st-key-selected_customer_card_status_contract_done_"] button::after {
            content: "계약 완료";
            color: #BBF7D0;
            background: rgba(34, 197, 94, 0.20);
            border-color: rgba(74, 222, 128, 0.42);
        }

        div[class*="st-key-customer_card_status_rejected_"] button,
        div[class*="st-key-selected_customer_card_status_rejected_"] button {
            border-left-color: #F87171 !important;
        }

        div[class*="st-key-customer_card_status_rejected_"] button::after,
        div[class*="st-key-selected_customer_card_status_rejected_"] button::after {
            content: "거절";
            color: #FECACA;
            background: rgba(239, 68, 68, 0.20);
            border-color: rgba(248, 113, 113, 0.42);
        }

        div[class*="st-key-customer_card_status_other_"] button,
        div[class*="st-key-selected_customer_card_status_other_"] button,
        div[class*="st-key-customer_card_status_default_"] button,
        div[class*="st-key-selected_customer_card_status_default_"] button {
            border-left-color: #94A3B8 !important;
        }

        div[class*="st-key-customer_card_status_other_"] button::after,
        div[class*="st-key-selected_customer_card_status_other_"] button::after {
            content: "기타";
            color: #E2E8F0;
            background: rgba(148, 163, 184, 0.18);
            border-color: rgba(148, 163, 184, 0.38);
        }

        div[class*="st-key-customer_card_status_default_"] button::after,
        div[class*="st-key-selected_customer_card_status_default_"] button::after {
            content: "상태 없음";
            color: #E2E8F0;
            background: rgba(148, 163, 184, 0.18);
            border-color: rgba(148, 163, 184, 0.38);
        }

        .customer-delete-zone {
            margin-top: 18px;
            padding: 20px;
            border-radius: 22px;
            background: rgba(15, 23, 42, 0.78);
            border: 1px solid rgba(248, 113, 113, 0.28);
        }

        .customer-delete-zone-title {
            font-size: 20px;
            font-weight: 850;
            color: #F8FAFC;
            letter-spacing: -0.04em;
            margin-bottom: 12px;
        }

        .customer-delete-zone-desc {
            color: #FCA5A5;
            font-size: 14px;
            margin-bottom: 12px;
        }

        .stTextInput input,
        .stTextArea textarea,
        .stDateInput input {
            background: #F8FAFC !important;
            color: #0F172A !important;
            border: 1px solid rgba(148, 163, 184, 0.40) !important;
            border-radius: 14px !important;
        }

        .stTextInput input::placeholder,
        .stTextArea textarea::placeholder {
            color: #64748B !important;
        }

        div[data-baseweb="select"] > div {
            background: #F8FAFC !important;
            color: #0F172A !important;
            border: 1px solid rgba(148, 163, 184, 0.40) !important;
            border-radius: 14px !important;
        }

        div[data-baseweb="select"] span {
            color: #0F172A !important;
        }

        div[data-baseweb="popover"] * {
            color: #0F172A !important;
        }

        div[data-testid="stAlert"] {
            background: rgba(30, 41, 59, 0.92) !important;
            color: #E5E7EB !important;
            border: 1px solid rgba(148, 163, 184, 0.24) !important;
        }

        div[data-testid="stAlert"] * {
            color: #E5E7EB !important;
        }

        @media screen and (max-width: 900px) {
            .customer-list-scroll-note {
                display: none;
            }

            div[class*="st-key-customer_card_status_"] button,
            div[class*="st-key-selected_customer_card_status_"] button {
                min-height: 74px !important;
                padding: 10px 96px 10px 12px !important;
            }

            div[class*="st-key-customer_card_status_"] button::after,
            div[class*="st-key-selected_customer_card_status_"] button::after {
                right: 9px;
                min-width: 66px;
                padding: 5px 6px;
                font-size: 10.5px;
            }

            div[class*="st-key-customer_card_status_"] button p,
            div[class*="st-key-selected_customer_card_status_"] button p {
                font-size: 12px !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def safe_value(value):
    return "" if value is None else str(value)


def safe_label(value, default="-"):
    text = safe_value(value).strip()

    if not text:
        text = default

    return re.sub(r"\s+", " ", text)


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


def get_birth_info_from_rrn(rrn):
    digits = only_digits(rrn)

    if len(digits) < 7:
        return None

    birth6 = digits[:6]
    gender_code = digits[6]

    try:
        yy = int(birth6[:2])
        mm = int(birth6[2:4])
        dd = int(birth6[4:6])
    except (TypeError, ValueError):
        return None

    if gender_code in ["1", "2", "5", "6"]:
        year = 1900 + yy
    elif gender_code in ["3", "4", "7", "8"]:
        year = 2000 + yy
    elif gender_code in ["9", "0"]:
        year = 1800 + yy
    else:
        return None

    try:
        return date(year, mm, dd)
    except ValueError:
        return None


def get_age_from_rrn(rrn):
    birthday = get_birth_info_from_rrn(rrn)

    if not birthday:
        return ""

    today = date.today()
    age = today.year - birthday.year

    if (today.month, today.day) < (birthday.month, birthday.day):
        age -= 1

    return f"만 {age}세"


def format_birth_from_rrn(rrn):
    birthday = get_birth_info_from_rrn(rrn)

    if not birthday:
        return "-"

    return birthday.strftime("%Y.%m.%d")


def short_address(address):
    text = safe_value(address).strip()

    if not text:
        return ""

    parts = text.split()

    if len(parts) >= 2:
        return f"{parts[0]} {parts[1]}"

    return text


def status_style_key(status):
    status_text = safe_value(status).strip()

    status_key_map = {
        "콜 대기": "call_wait",
        "콜 부재": "call_absent",
        "콜 거절": "call_reject",
        "상담 예정": "consult_scheduled",
        "상담 중": "consult_active",
        "설계 중": "design_active",
        "증권 전달": "policy_delivered",
        "계약 완료": "contract_done",
        "거절": "rejected",
        "기타": "other",
    }

    return status_key_map.get(status_text, "default")


def get_consult_first_line(text):
    value = safe_value(text).strip()

    if not value:
        return "상담 내용 없음"

    first_line = value.splitlines()[0].strip()

    if len(first_line) > 35:
        return first_line[:35] + "..."

    return first_line


def render_consult_content_box(text):
    safe_text = safe_html(text, "내용 없음")

    st.markdown(
        f"""
        <div class="crm-content-box">
            {safe_text}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_customer_consult_logs(selected_customer_id):
    logs = get_consult_logs(selected_customer_id)

    st.markdown(
        '<div class="customer-consult-divider"></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="customer-consult-heading">
            상담 이력 조회
            <span class="customer-consult-count">{len(logs)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not logs:
        st.info("등록된 상담 이력이 없습니다.")
        return

    for log in logs:
        first_line = get_consult_first_line(log.get("content"))

        title_parts = [
            safe_value(log.get("consult_date")),
            first_line,
        ]

        if log.get("next_action_date"):
            if log.get("next_action"):
                title_parts.append(
                    f"다음연락: {log.get('next_action_date')} / "
                    f"{log.get('next_action')}"
                )
            else:
                title_parts.append(
                    f"다음연락: {log.get('next_action_date')}"
                )

        writer_name = safe_value(log.get("writer_name")).strip()

        if writer_name:
            title_parts.append(f"작성자: {writer_name}")

        expander_title = " / ".join(
            part for part in title_parts if part
        )

        with st.expander(expander_title):
            render_section_title("상담 내용")
            render_consult_content_box(log.get("content"))

            if log.get("next_action_date"):
                render_section_title("다음 연락 예정일")

                next_contact_text = safe_value(
                    log.get("next_action_date")
                )

                if log.get("next_action"):
                    next_contact_text += (
                        f" / {log.get('next_action')}"
                    )

                render_consult_content_box(next_contact_text)

            created_at = safe_value(log.get("created_at"))

            if created_at:
                st.markdown(
                    f"""
                    <div class="customer-consult-meta">
                        등록일: {html.escape(created_at)}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


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

    birth = format_birth_from_rrn(customer.get("rrn"))

    searchable_values = [
        customer.get("name"),
        customer.get("phone"),
        customer.get("carrier"),
        customer.get("rrn"),
        birth,
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
        customer_type = safe_value(
            customer.get("customer_type")
        ).strip()

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

    with st.container(border=True):
        render_section_title("고객 필터")

        col_search, col_status, col_type, col_reset = st.columns(
            [0.38, 0.22, 0.22, 0.18]
        )

        with col_search:
            keyword = st.text_input(
                "검색",
                placeholder="고객명, 연락처, 생년월일, 주소, 메모 검색",
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
                전체 {len(customers)}명 중
                {len(filtered_customers)}명이 표시됩니다.
            </div>
            """,
            unsafe_allow_html=True,
        )

    return filtered_customers


def render_customer_card(customer, is_selected):
    customer_id = customer["id"]

    name = safe_label(customer.get("name"), "이름없음")
    age = safe_label(
        get_age_from_rrn(customer.get("rrn")),
        "만 나이 없음",
    )
    phone = safe_label(
        format_phone_with_carrier(
            customer.get("phone"),
            customer.get("carrier"),
        ),
        "연락처 없음",
    )
    birth = safe_label(
        format_birth_from_rrn(customer.get("rrn")),
        "-",
    )
    address = safe_label(
        short_address(customer.get("address")),
        "-",
    )
    status = safe_label(
        customer.get("status"),
        "상태 없음",
    )

    style_key = status_style_key(status)

    card_label = (
        f"**{name} ({age})**   {phone}\n"
        f"생년월일 {birth}   ·   주소 {address}"
    )

    if is_selected:
        button_key = (
            f"selected_customer_card_status_"
            f"{style_key}_{customer_id}"
        )
    else:
        button_key = (
            f"customer_card_status_"
            f"{style_key}_{customer_id}"
        )

    if st.button(
        card_label,
        key=button_key,
        use_container_width=True,
        help=f"{status} · 클릭하면 오른쪽에 상세 정보가 표시됩니다.",
    ):
        st.session_state.selected_customer_id = customer_id
        st.rerun()


def render_customer_detail_form(
    customer,
    selected_customer_id,
    user,
):
    render_section_title("고객 상세 / 수정")

    age_text = (
        get_age_from_rrn(customer.get("rrn"))
        or "만 나이 계산 불가"
    )

    with st.form(
        f"customer_detail_edit_form_{selected_customer_id}"
    ):
        col1, col2 = st.columns(2)

        current_type = (
            customer.get("customer_type")
            or CUSTOMER_TYPE_OPTIONS[0]
        )
        current_status = (
            customer.get("status")
            or STATUS_OPTIONS[0]
        )
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

            owner_name = safe_value(
                customer.get("owner_name")
            )
            created_at = safe_value(
                customer.get("created_at")
            )

            st.text_input(
                "담당자",
                value=owner_name,
                disabled=True,
            )

            st.text_input(
                "등록일",
                value=created_at,
                disabled=True,
            )

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
                "상담 이력 등록 / 관리",
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
            st.session_state.selected_consult_customer_id = (
                selected_customer_id
            )
            st.switch_page("pages/4_상담이력.py")

    render_customer_consult_logs(selected_customer_id)

    st.markdown(
        """
        <div class="customer-consult-divider"></div>
        <div class="customer-delete-zone">
            <div class="customer-delete-zone-title">
                고객 삭제
            </div>
            <div class="customer-delete-zone-desc">
                고객을 삭제하면 해당 고객의 상담 이력도 함께 삭제됩니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    confirm_text = st.text_input(
        "삭제하려면 고객명을 그대로 입력하세요.",
        key=f"delete_confirm_{selected_customer_id}",
    )

    if st.button(
        "고객 삭제",
        key=f"delete_customer_{selected_customer_id}",
        use_container_width=True,
    ):
        customer_name = safe_value(
            customer.get("name")
        ).strip()

        if confirm_text.strip() != customer_name:
            st.error(
                "고객명이 일치하지 않아 삭제하지 않았습니다."
            )
        else:
            deleted = delete_customer(
                selected_customer_id,
                user,
            )

            if deleted:
                st.success("고객이 삭제되었습니다.")
                st.session_state.selected_customer_id = None
                st.rerun()
            else:
                st.error(
                    "삭제 권한이 없거나 고객을 찾을 수 없습니다."
                )


def render_customer_list_area(filtered_customers):
    with st.container(border=True):
        render_section_title("고객 목록")

        st.caption(
            "고객 카드를 클릭하면 오른쪽에서 상세 수정이 가능합니다."
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
                st.info(
                    "필터 조건에 맞는 고객이 없습니다."
                )
            else:
                for customer in filtered_customers:
                    is_selected = (
                        st.session_state.selected_customer_id
                        == customer["id"]
                    )

                    render_customer_card(
                        customer,
                        is_selected,
                    )


def render_customer_detail_area(
    user,
    selected_customer_id,
):
    with st.container(border=True):
        if not selected_customer_id:
            render_section_title("상세 정보")

            st.info(
                "상세보기 또는 수정을 하려면 고객 카드를 클릭하세요."
            )
            return

        customer = get_customer_by_id(
            selected_customer_id
        )

        if not customer:
            render_section_title("상세 정보")

            st.warning(
                "고객 정보를 찾을 수 없습니다."
            )
            return

        render_customer_detail_form(
            customer,
            selected_customer_id,
            user,
        )


def customer_list_page(user):
    inject_customer_list_css()

    render_page_header(
        "고객 리스트",
        (
            "등록된 고객을 필터로 정리하고 고객 카드를 클릭해 "
            "상세 정보를 관리하세요."
        ),
    )

    customers = get_customers(user)

    if not customers:
        st.info("등록된 고객이 없습니다.")
        return

    if "selected_customer_id" not in st.session_state:
        st.session_state.selected_customer_id = None

    all_customer_ids = [
        customer["id"]
        for customer in customers
    ]

    if (
        st.session_state.selected_customer_id
        not in all_customer_ids
    ):
        st.session_state.selected_customer_id = None

    filtered_customers = render_customer_filters(
        customers
    )

    filtered_customer_ids = [
        customer["id"]
        for customer in filtered_customers
    ]

    if (
        st.session_state.selected_customer_id
        and st.session_state.selected_customer_id
        not in filtered_customer_ids
    ):
        st.session_state.selected_customer_id = None

    st.markdown(
        "<br>",
        unsafe_allow_html=True,
    )

    left, right = st.columns(
        [0.88, 1.12],
    )

    with left:
        render_customer_list_area(
            filtered_customers
        )

    with right:
        render_customer_detail_area(
            user=user,
            selected_customer_id=(
                st.session_state.selected_customer_id
            ),
        )