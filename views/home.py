import calendar
import html
from collections import defaultdict
from datetime import date, datetime

import streamlit as st
import streamlit.components.v1 as components

from utils.ui import (
    inject_global_css,
    render_page_header,
    render_metric_card,
    render_section_title,
    render_card_start,
    render_card_end,
)
from utils.customer import get_customers
from utils.consult import get_month_next_actions
from utils.schedule import (
    add_general_schedule,
    update_general_schedule,
    delete_general_schedule,
    get_month_general_schedules,
)


def _safe_text(value, default="-"):
    if value is None:
        return default

    value = str(value).strip()

    if not value:
        return default

    return value


def _safe_html(value, default="-"):
    return html.escape(_safe_text(value, default))


def _parse_date(value):
    if not value:
        return None

    value = str(value).strip()

    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def _count_by_status(customers, keyword):
    count = 0

    for customer in customers:
        status = str(customer.get("status", "")).strip()

        if keyword in status:
            count += 1

    return count


def _get_query_calendar_date():
    try:
        value = st.query_params.get("calendar_date")
    except Exception:
        value = None

    if isinstance(value, list):
        value = value[0] if value else None

    return _parse_date(value)


def _set_query_calendar_date(selected_date):
    try:
        st.query_params["calendar_date"] = selected_date.isoformat()
    except Exception:
        pass


def _init_calendar_state():
    today = date.today()

    if "calendar_year" not in st.session_state:
        st.session_state.calendar_year = today.year

    if "calendar_month" not in st.session_state:
        st.session_state.calendar_month = today.month

    if "selected_calendar_date" not in st.session_state:
        st.session_state.selected_calendar_date = today.isoformat()

    if "editing_general_schedule_id" not in st.session_state:
        st.session_state.editing_general_schedule_id = None

    query_date = _get_query_calendar_date()

    if query_date:
        st.session_state.selected_calendar_date = query_date.isoformat()
        st.session_state.calendar_year = query_date.year
        st.session_state.calendar_month = query_date.month


def _get_selected_date():
    selected = st.session_state.get("selected_calendar_date")
    parsed = _parse_date(selected)

    if parsed:
        return parsed

    return date.today()


def _set_selected_date(selected_date):
    st.session_state.selected_calendar_date = selected_date.isoformat()
    st.session_state.calendar_year = selected_date.year
    st.session_state.calendar_month = selected_date.month
    st.session_state.editing_general_schedule_id = None
    _set_query_calendar_date(selected_date)


def _group_customer_actions_by_day(customer_actions):
    grouped = defaultdict(list)

    for action in customer_actions:
        action_date = _parse_date(action.get("next_action_date"))

        if action_date:
            grouped[action_date.day].append(action)

    return grouped


def _group_general_schedules_by_day(general_schedules):
    grouped = defaultdict(list)

    for schedule in general_schedules:
        schedule_date = _parse_date(schedule.get("schedule_date"))

        if schedule_date:
            grouped[schedule_date.day].append(schedule)

    return grouped


def _get_customer_actions_for_date(customer_actions, target_date):
    result = []

    for action in customer_actions:
        action_date = _parse_date(action.get("next_action_date"))

        if action_date == target_date:
            result.append(action)

    return result


def _get_general_schedules_for_date(general_schedules, target_date):
    result = []

    for schedule in general_schedules:
        schedule_date = _parse_date(schedule.get("schedule_date"))

        if schedule_date == target_date:
            result.append(schedule)

    return result


def _render_month_selector():
    _init_calendar_state()

    left, center, right = st.columns([0.18, 0.64, 0.18])

    with left:
        if st.button(
            "◀ 이전달",
            use_container_width=True,
            key="calendar_prev_month",
        ):
            if st.session_state.calendar_month == 1:
                st.session_state.calendar_month = 12
                st.session_state.calendar_year -= 1
            else:
                st.session_state.calendar_month -= 1

            first_day = date(
                st.session_state.calendar_year,
                st.session_state.calendar_month,
                1,
            )
            _set_selected_date(first_day)
            st.rerun()

    with center:
        st.markdown(
            f"""
            <div class="calendar-month-title">
                {st.session_state.calendar_year}년 {st.session_state.calendar_month}월
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        if st.button(
            "다음달 ▶",
            use_container_width=True,
            key="calendar_next_month",
        ):
            if st.session_state.calendar_month == 12:
                st.session_state.calendar_month = 1
                st.session_state.calendar_year += 1
            else:
                st.session_state.calendar_month += 1

            first_day = date(
                st.session_state.calendar_year,
                st.session_state.calendar_month,
                1,
            )
            _set_selected_date(first_day)
            st.rerun()

    return st.session_state.calendar_year, st.session_state.calendar_month


def _build_calendar_event_html(customer_actions, general_schedules):
    event_html_list = []

    for action in customer_actions[:2]:
        customer_name = _safe_html(action.get("customer_name"))
        next_action = _safe_html(action.get("next_action"), "상담 예정")

        event_html_list.append(
            f"""
            <div class="calendar-table-event calendar-table-customer">
                <div class="calendar-table-type">고객</div>
                <div class="calendar-table-event-name">{customer_name}</div>
                <div class="calendar-table-event-desc">{next_action}</div>
            </div>
            """
        )

    for schedule in general_schedules[:2]:
        title = _safe_html(schedule.get("title"), "일반일정")

        event_html_list.append(
            f"""
            <div class="calendar-table-event calendar-table-general">
                <div class="calendar-table-type">일반</div>
                <div class="calendar-table-event-name">{title}</div>
            </div>
            """
        )

    total_count = len(customer_actions) + len(general_schedules)
    shown_count = min(len(customer_actions), 2) + min(len(general_schedules), 2)

    if total_count > shown_count:
        event_html_list.append(
            f"""
            <div class="calendar-table-more">
                +{total_count - shown_count}건 더 있음
            </div>
            """
        )

    return "".join(event_html_list)


def _build_calendar_html(year, month, customer_actions, general_schedules, selected_date):
    customer_grouped = _group_customer_actions_by_day(customer_actions)
    general_grouped = _group_general_schedules_by_day(general_schedules)

    today = date.today()

    cal = calendar.Calendar(firstweekday=6)
    weeks = cal.monthdayscalendar(year, month)

    weekday_names = ["일", "월", "화", "수", "목", "금", "토"]

    header_cells = ""

    for weekday in weekday_names:
        header_cells += f"""
        <th class="calendar-table-weekday">{weekday}</th>
        """

    body_rows = ""

    for week in weeks:
        body_rows += "<tr>"

        for day in week:
            if day == 0:
                body_rows += """
                <td class="calendar-table-cell calendar-table-empty"></td>
                """
                continue

            current_date = date(year, month, day)
            current_date_text = current_date.isoformat()

            day_customer_actions = customer_grouped.get(day, [])
            day_general_schedules = general_grouped.get(day, [])

            event_html = _build_calendar_event_html(
                day_customer_actions,
                day_general_schedules,
            )

            today_class = ""
            selected_class = ""

            if today == current_date:
                today_class = " calendar-table-today"

            if selected_date == current_date:
                selected_class = " calendar-table-selected"

            customer_count = len(day_customer_actions)
            general_count = len(day_general_schedules)

            count_html = ""

            if customer_count or general_count:
                count_parts = []

                if customer_count:
                    count_parts.append(f"고객 {customer_count}")

                if general_count:
                    count_parts.append(f"일반 {general_count}")

                count_html = f"""
                <span class="calendar-table-count">{" / ".join(count_parts)}</span>
                """

            body_rows += f"""
            <td class="calendar-table-cell{today_class}{selected_class}">
                <a
                    class="calendar-table-link"
                    href="?calendar_date={current_date_text}"
                    target="_parent"
                    title="{current_date_text}"
                >
                    <div class="calendar-table-day-head">
                        <span class="calendar-table-day-number">{day}</span>
                        {count_html}
                    </div>
                    <div class="calendar-table-events">
                        {event_html}
                    </div>
                </a>
            </td>
            """

        body_rows += "</tr>"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            * {{
                box-sizing: border-box;
            }}

            body {{
                margin: 0;
                padding: 0;
                background: transparent;
                font-family:
                    -apple-system,
                    BlinkMacSystemFont,
                    "Segoe UI",
                    sans-serif;
            }}

            .calendar-table-wrap {{
                width: 100%;
                padding: 18px;
                background: rgba(15, 23, 42, 0.62);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 24px;
                box-shadow: 0 18px 60px rgba(0, 0, 0, 0.22);
                overflow-x: auto;
            }}

            .calendar-table {{
                width: 100%;
                border-collapse: separate;
                border-spacing: 10px;
                table-layout: fixed;
            }}

            .calendar-table-weekday {{
                color: #CBD5E1;
                font-size: 13px;
                font-weight: 850;
                text-align: center;
                padding: 8px 0 10px 0;
            }}

            .calendar-table-cell {{
                height: 142px;
                vertical-align: top;
                background: rgba(255, 255, 255, 0.045);
                border: 1px solid rgba(255, 255, 255, 0.085);
                border-radius: 18px;
                padding: 0;
                overflow: hidden;
                transition: 0.15s ease;
            }}

            .calendar-table-cell:hover {{
                background: rgba(255, 255, 255, 0.07);
                border-color: rgba(148, 163, 184, 0.24);
                transform: translateY(-1px);
            }}

            .calendar-table-empty {{
                opacity: 0.22;
                background: rgba(255, 255, 255, 0.025);
                pointer-events: none;
            }}

            .calendar-table-link {{
                display: block;
                width: 100%;
                height: 142px;
                padding: 12px;
                text-decoration: none;
                color: inherit;
                cursor: pointer;
            }}

            .calendar-table-link:hover {{
                text-decoration: none;
            }}

            .calendar-table-today {{
                border-color: rgba(91, 140, 255, 0.72);
                box-shadow: 0 0 0 1px rgba(91, 140, 255, 0.32);
                background:
                    linear-gradient(135deg, rgba(91, 140, 255, 0.13), rgba(124, 92, 255, 0.07)),
                    rgba(255, 255, 255, 0.055);
            }}

            .calendar-table-selected {{
                border-color: rgba(34, 197, 94, 0.78);
                box-shadow: 0 0 0 2px rgba(34, 197, 94, 0.28);
            }}

            .calendar-table-day-head {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 6px;
                margin-bottom: 8px;
            }}

            .calendar-table-day-number {{
                color: #F8FAFC;
                font-size: 15px;
                font-weight: 900;
                flex-shrink: 0;
            }}

            .calendar-table-count {{
                background: rgba(255, 255, 255, 0.11);
                color: #E2E8F0;
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 999px;
                padding: 2px 7px;
                font-size: 10px;
                font-weight: 850;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }}

            .calendar-table-events {{
                display: flex;
                flex-direction: column;
                gap: 6px;
            }}

            .calendar-table-event {{
                border-radius: 12px;
                padding: 6px 8px;
            }}

            .calendar-table-customer {{
                background: rgba(59, 130, 246, 0.14);
                border: 1px solid rgba(96, 165, 250, 0.28);
            }}

            .calendar-table-general {{
                background: rgba(34, 197, 94, 0.14);
                border: 1px solid rgba(74, 222, 128, 0.26);
            }}

            .calendar-table-type {{
                display: inline-block;
                color: #F8FAFC;
                background: rgba(255, 255, 255, 0.13);
                border-radius: 999px;
                padding: 2px 6px;
                font-size: 9px;
                font-weight: 900;
                margin-bottom: 3px;
            }}

            .calendar-table-event-name {{
                color: #F8FAFC;
                font-size: 12px;
                font-weight: 800;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }}

            .calendar-table-event-desc {{
                color: #CBD5E1;
                font-size: 11px;
                margin-top: 2px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }}

            .calendar-table-more {{
                color: #94A3B8;
                font-size: 11px;
                padding-left: 4px;
            }}
        </style>
    </head>
    <body>
        <div class="calendar-table-wrap">
            <table class="calendar-table">
                <thead>
                    <tr>
                        {header_cells}
                    </tr>
                </thead>
                <tbody>
                    {body_rows}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """


def _render_calendar(year, month, customer_actions, general_schedules):
    selected_date = _get_selected_date()

    calendar_html = _build_calendar_html(
        year,
        month,
        customer_actions,
        general_schedules,
        selected_date,
    )

    components.html(
        calendar_html,
        height=860,
        scrolling=False,
    )


def _render_customer_schedule_list(selected_customer_actions):
    render_section_title("고객일정")

    if not selected_customer_actions:
        st.info("선택한 날짜에 고객일정이 없습니다.")
        return

    for action in selected_customer_actions:
        customer_name = _safe_html(action.get("customer_name"))
        customer_phone = _safe_html(action.get("customer_phone"), "연락처 없음")
        next_action = _safe_html(action.get("next_action"), "상담 예정")
        owner_name = _safe_html(action.get("owner_name"), "담당자 없음")

        st.markdown(
            f"""
            <div class="schedule-panel-card schedule-customer-card">
                <div>
                    <div class="schedule-panel-type customer-type">고객일정</div>
                    <div class="today-action-title">{customer_name}</div>
                    <div class="today-action-meta">{customer_phone}</div>
                </div>
                <div class="today-action-right">
                    <div class="today-action-badge">{next_action}</div>
                    <div class="today-action-owner">{owner_name}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button(
            "상담 이력에서 수정",
            key=f"edit_customer_schedule_{action.get('id')}",
            use_container_width=True,
        ):
            st.session_state.selected_consult_customer_id = action.get("customer_id")
            st.switch_page("pages/4_상담이력.py")


def _render_general_schedule_list(selected_general_schedules):
    render_section_title("일반일정")

    if not selected_general_schedules:
        st.info("선택한 날짜에 일반일정이 없습니다.")
        return

    for schedule in selected_general_schedules:
        title = _safe_html(schedule.get("title"), "일반일정")
        content = _safe_html(schedule.get("content"), "")
        owner_name = _safe_html(schedule.get("owner_name"), "작성자 없음")

        st.markdown(
            f"""
            <div class="schedule-panel-card schedule-general-card">
                <div>
                    <div class="schedule-panel-type general-type">일반일정</div>
                    <div class="today-action-title">{title}</div>
                    <div class="today-action-meta">{content}</div>
                    <div class="today-action-owner">작성자: {owner_name}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_edit, col_delete = st.columns(2)

        with col_edit:
            if st.button(
                "수정",
                key=f"edit_general_schedule_{schedule.get('id')}",
                use_container_width=True,
            ):
                st.session_state.editing_general_schedule_id = schedule.get("id")
                st.rerun()

        with col_delete:
            if st.button(
                "삭제",
                key=f"delete_general_schedule_{schedule.get('id')}",
                use_container_width=True,
            ):
                deleted = delete_general_schedule(
                    schedule.get("id"),
                    st.session_state.user,
                )

                if deleted:
                    st.success("일반일정이 삭제되었습니다.")
                    st.session_state.editing_general_schedule_id = None
                    st.rerun()
                else:
                    st.error("삭제 권한이 없거나 일정을 찾을 수 없습니다.")


def _find_general_schedule(general_schedules, schedule_id):
    for schedule in general_schedules:
        if schedule.get("id") == schedule_id:
            return schedule

    return None


def _render_general_schedule_form(user, selected_date, selected_general_schedules):
    editing_id = st.session_state.get("editing_general_schedule_id")
    editing_schedule = None

    if editing_id:
        editing_schedule = _find_general_schedule(
            selected_general_schedules,
            editing_id,
        )

    if editing_schedule:
        render_section_title("일반일정 수정")
        default_title = _safe_text(editing_schedule.get("title"), "")
        default_content = _safe_text(editing_schedule.get("content"), "")
        default_date = _parse_date(editing_schedule.get("schedule_date")) or selected_date
        button_label = "일반일정 수정 저장"
        form_key = f"general_schedule_edit_form_{editing_id}"
        show_cancel = True
    else:
        render_section_title("일반일정 추가")
        default_title = ""
        default_content = ""
        default_date = selected_date
        button_label = "일반일정 추가"
        form_key = f"general_schedule_add_form_{selected_date.isoformat()}"
        show_cancel = False

    with st.form(form_key):
        schedule_date = st.date_input(
            "일정 날짜",
            value=default_date,
            key=f"{form_key}_date",
        )

        title = st.text_input(
            "일정 제목",
            value=default_title,
            placeholder="예: 지점 회의, 고객자료 정리, 교육 참석",
            key=f"{form_key}_title",
        )

        content = st.text_area(
            "일정 내용",
            value=default_content,
            placeholder="일정 상세 내용을 입력하세요.",
            height=100,
            key=f"{form_key}_content",
        )

        if show_cancel:
            col_save, col_cancel = st.columns(2)

            with col_save:
                submitted = st.form_submit_button(
                    button_label,
                    use_container_width=True,
                )

            with col_cancel:
                cancel = st.form_submit_button(
                    "수정 취소",
                    use_container_width=True,
                )
        else:
            submitted = st.form_submit_button(
                button_label,
                use_container_width=True,
            )
            cancel = False

        if submitted:
            if not title.strip():
                st.warning("일정 제목을 입력하세요.")
            else:
                if editing_schedule:
                    updated = update_general_schedule(
                        schedule_id=editing_id,
                        user=user,
                        schedule_date=str(schedule_date),
                        title=title.strip(),
                        content=content.strip(),
                    )

                    if updated:
                        st.success("일반일정이 수정되었습니다.")
                        st.session_state.editing_general_schedule_id = None
                        st.rerun()
                    else:
                        st.error("수정 권한이 없거나 일정을 찾을 수 없습니다.")
                else:
                    add_general_schedule(
                        user_id=user["id"],
                        schedule_date=str(schedule_date),
                        title=title.strip(),
                        content=content.strip(),
                    )

                    st.success("일반일정이 추가되었습니다.")
                    st.rerun()

        if cancel:
            st.session_state.editing_general_schedule_id = None
            st.rerun()


def _render_selected_day_panel(user, customer_actions, general_schedules):
    selected_date = _get_selected_date()

    selected_customer_actions = _get_customer_actions_for_date(
        customer_actions,
        selected_date,
    )
    selected_general_schedules = _get_general_schedules_for_date(
        general_schedules,
        selected_date,
    )

    render_card_start()

    st.markdown(
        f"""
        <div class="crm-hero-title" style="font-size:24px;">
            {selected_date.year}년 {selected_date.month}월 {selected_date.day}일
        </div>
        <div class="crm-muted">
            달력에서 날짜를 클릭하면 해당 날짜의 고객일정과 일반일정을 확인할 수 있습니다.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    _render_customer_schedule_list(selected_customer_actions)

    st.markdown("<br>", unsafe_allow_html=True)

    _render_general_schedule_list(selected_general_schedules)

    st.markdown("<br>", unsafe_allow_html=True)

    _render_general_schedule_form(
        user,
        selected_date,
        selected_general_schedules,
    )

    render_card_end()


def home_page(user):
    inject_global_css()

    _init_calendar_state()

    customers = get_customers(user)

    total_customers = len(customers)
    active_customers = _count_by_status(customers, "진행")

    render_page_header(
        "상담 일정 Dashboard",
        f"{user.get('name', '사용자')}님, 고객일정과 일반일정을 한 화면에서 관리하세요.",
    )

    year, month = _render_month_selector()

    customer_actions = get_month_next_actions(user, year, month)
    general_schedules = get_month_general_schedules(user, year, month)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_metric_card(
            label="전체 고객",
            value=total_customers,
            desc="등록된 고객 수",
        )

    with col2:
        render_metric_card(
            label="고객일정",
            value=len(customer_actions),
            desc="상담 이력 다음 연락일 기준",
        )

    with col3:
        render_metric_card(
            label="일반일정",
            value=len(general_schedules),
            desc="메인 달력 직접 등록 일정",
        )

    with col4:
        render_metric_card(
            label="진행 고객",
            value=active_customers,
            desc="상태에 '진행' 포함",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    left, right = st.columns([1.45, 0.95])

    with left:
        _render_calendar(
            year,
            month,
            customer_actions,
            general_schedules,
        )

    with right:
        _render_selected_day_panel(
            user,
            customer_actions,
            general_schedules,
        )