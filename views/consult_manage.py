import streamlit as st
from datetime import date

from utils.customer import get_customers
from utils.consult import add_consult_log, get_consult_logs


def init_consult_state():
    if "selected_consult_customer_id" not in st.session_state:
        st.session_state.selected_consult_customer_id = None


def get_first_line(text):
    value = str(text or "").strip()

    if not value:
        return "상담 내용 없음"

    first_line = value.splitlines()[0].strip()

    if len(first_line) > 35:
        return first_line[:35] + "..."

    return first_line


def render_section_title(title):
    st.markdown(
        f"""
        <div style="
            margin-top: 8px;
            margin-bottom: 8px;
            padding: 8px 10px;
            border-left: 4px solid #4F46E5;
            background-color: rgba(79, 70, 229, 0.08);
            font-weight: 700;
        ">
            {title}
        </div>
        """,
        unsafe_allow_html=True
    )


def render_content_box(text):
    safe_text = (
        str(text or "")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    st.markdown(
        f"""
        <div style="
            padding: 12px;
            border: 1px solid rgba(120, 120, 120, 0.35);
            border-radius: 8px;
            background-color: rgba(250, 250, 250, 0.04);
            white-space: pre-wrap;
            line-height: 1.6;
        ">
            {safe_text}
        </div>
        """,
        unsafe_allow_html=True
    )


def consult_manage_page(user):
    init_consult_state()

    st.subheader("상담 이력 관리")

    customers = get_customers(user)

    if not customers:
        st.info("상담 이력을 등록할 고객이 없습니다.")
        return

    customer_options = {"(선택)": None}

    for customer in customers:
        label = (
            f"{customer['name']} / "
            f"{customer.get('phone') or '연락처 없음'} / "
            f"{customer.get('status') or '상태 없음'}"
        )
        customer_options[label] = customer["id"]

    option_labels = list(customer_options.keys())
    customer_ids = list(customer_options.values())

    default_index = 0

    if st.session_state.selected_consult_customer_id in customer_ids:
        default_index = customer_ids.index(
            st.session_state.selected_consult_customer_id
        )

    selected_label = st.selectbox(
        "고객 선택",
        option_labels,
        index=default_index
    )

    selected_customer_id = customer_options[selected_label]
    st.session_state.selected_consult_customer_id = selected_customer_id

    if selected_customer_id is None:
        st.info("상담 이력을 등록하거나 조회할 고객을 선택하세요.")
        return

    selected_customer_name = selected_label.split(" / ")[0]

    nonce_key = f"consult_nonce_{selected_customer_id}"

    if nonce_key not in st.session_state:
        st.session_state[nonce_key] = 0

    nonce = st.session_state[nonce_key]

    st.divider()
    st.subheader("상담 내용 등록")

    consult_date = st.date_input(
        "상담일",
        value=date.today(),
        key=f"consult_date_{selected_customer_id}_{nonce}"
    )

    content = st.text_area(
        "상담 내용",
        height=180,
        key=f"consult_content_{selected_customer_id}_{nonce}"
    )

    st.markdown("---")

    use_next_action_date = st.checkbox(
        "다음 연락일 등록",
        value=False,
        key=f"use_next_action_date_{selected_customer_id}_{nonce}"
    )

    next_action_date = None
    next_action = ""

    if use_next_action_date:
        next_action_date = st.date_input(
            "다음 연락 예정일",
            value=date.today(),
            key=f"next_action_date_{selected_customer_id}_{nonce}"
        )

        next_action = st.text_input(
            "다음 연락 내용",
            placeholder="예: 상담 예정, 증권 요청, 리모델링 제안서 전달",
            key=f"next_action_{selected_customer_id}_{nonce}"
        )

    submitted = st.button(
        "상담 이력 저장",
        use_container_width=True,
        key=f"save_consult_{selected_customer_id}_{nonce}"
    )

    if submitted:
        if not content.strip():
            st.warning("상담 내용을 입력하세요.")
        else:
            next_action_date_text = ""

            if use_next_action_date:
                next_action_date_text = str(next_action_date)

            add_consult_log(
                customer_id=selected_customer_id,
                user_id=user["id"],
                consult_date=str(consult_date),
                content=content.strip(),
                next_action=next_action.strip(),
                next_action_date=next_action_date_text
            )

            st.session_state[nonce_key] += 1

            if use_next_action_date:
                st.success(
                    f"{selected_customer_name}님 {next_action.strip() or '다음 연락'} 일정이 등록되었습니다."
                )
            else:
                st.success("상담 이력이 저장되었습니다.")

            st.rerun()

    st.divider()
    st.subheader("상담 이력 조회")

    logs = get_consult_logs(selected_customer_id)

    if not logs:
        st.info("등록된 상담 이력이 없습니다.")
        return

    for log in logs:
        first_line = get_first_line(log.get("content"))

        title_parts = [
            str(log.get("consult_date") or ""),
            first_line
        ]

        if log.get("next_action_date"):
            if log.get("next_action"):
                title_parts.append(
                    f"다음연락: {log.get('next_action_date')} / {log.get('next_action')}"
                )
            else:
                title_parts.append(
                    f"다음연락: {log.get('next_action_date')}"
                )

        title_parts.append(f"작성자: {log.get('writer_name') or ''}")

        with st.expander(" / ".join(title_parts)):
            render_section_title("상담 내용")
            render_content_box(log.get("content"))

            if log.get("next_action_date"):
                render_section_title("다음 연락 예정일")

                next_contact_text = log.get("next_action_date")

                if log.get("next_action"):
                    next_contact_text += f" / {log.get('next_action')}"

                render_content_box(next_contact_text)

            st.caption(f"등록일: {log['created_at']}")