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
)
from utils.customer import get_customers
from utils.consult import get_month_next_actions


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


def _group_actions_by_day(actions):
    grouped = defaultdict(list)

    for action in actions:
        action_date = _parse_date(action.get("next_action_date"))

        if action_date:
            grouped[action_date.day].append(action)

    return grouped


def _render_month_selector():
    today = date.today()

    if "calendar_year" not in st.session_state:
        st.session_state.calendar_year = today.year

    if "calendar_month" not in st.session_state:
        st.session_state.calendar_month = today.month

    left, center, right = st.columns([0.18, 0.64, 0.18])

    with left:
        if st.button("◀ 이전달", use_container_width=True):
            if st.session_state.calendar_month == 1:
                st.session_state.calendar_month = 12
                st.session_state.calendar_year -= 1
            else:
                st.session_state.calendar_month -= 1

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
        if st.button("다음달 ▶", use_container_width=True):
            if st.session_state.calendar_month == 12:
                st.session_state.calendar_month = 1
                st.session_state.calendar_year += 1
            else:
                st.session_state.calendar_month += 1

            st.rerun()

    return st.session_state.calendar_year, st.session_state.calendar_month


def _build_event_html(actions):
    if not actions:
        return ""

    event_html_list = []

    for action in actions[:2]:
        customer_name = _safe_html(action.get("customer_name"))
        next_action = _safe_html(action.get("next_action"), "상담 예정")

        event_html_list.append(
            f"""
            <div class="calendar-table-event">
                <div class="calendar-table-event-name">{customer_name}</div>
                <div class="calendar-table-event-desc">{next_action}</div>
            </div>
            """
        )

    if len(actions) > 2:
        event_html_list.append(
            f"""
            <div class="calendar-table-more">
                +{len(actions) - 2}건 더 있음
            </div>
            """
        )

    return "".join(event_html_list)


def _build_calendar_html(year, month, actions):
    grouped = _group_actions_by_day(actions)
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

            day_actions = grouped.get(day, [])
            event_html = _build_event_html(day_actions)

            today_class = ""

            if (
                today.year == year
                and today.month == month
                and today.day == day
            ):
                today_class = " calendar-table-today"

            count_html = ""

            if day_actions:
                count_html = f"""
                <span class="calendar-table-count">{len(day_actions)}</span>
                """

            body_rows += f"""
            <td class="calendar-table-cell{today_class}">
                <div class="calendar-table-day-head">
                    <span class="calendar-table-day-number">{day}</span>
                    {count_html}
                </div>
                <div class="calendar-table-events">
                    {event_html}
                </div>
            </td>
            """

        body_rows += "</tr>"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
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
                box-sizing: border-box;
                width: 100%;
                padding: 18px;
                background: rgba(15, 23, 42, 0.62);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 24px;
                box-shadow: 0 18px 60px rgba(0, 0, 0, 0.22);
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
                height: 128px;
                vertical-align: top;
                background: rgba(255, 255, 255, 0.045);
                border: 1px solid rgba(255, 255, 255, 0.085);
                border-radius: 18px;
                padding: 12px;
                overflow: hidden;
                transition: 0.15s ease;
            }}

            .calendar-table-cell:hover {{
                background: rgba(255, 255, 255, 0.07);
                border-color: rgba(148, 163, 184, 0.24);
            }}

            .calendar-table-empty {{
                opacity: 0.22;
                background: rgba(255, 255, 255, 0.025);
            }}

            .calendar-table-today {{
                border-color: rgba(91, 140, 255, 0.72);
                box-shadow: 0 0 0 1px rgba(91, 140, 255, 0.32);
                background:
                    linear-gradient(135deg, rgba(91, 140, 255, 0.13), rgba(124, 92, 255, 0.07)),
                    rgba(255, 255, 255, 0.055);
            }}

            .calendar-table-day-head {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 8px;
            }}

            .calendar-table-day-number {{
                color: #F8FAFC;
                font-size: 15px;
                font-weight: 900;
            }}

            .calendar-table-count {{
                background: linear-gradient(135deg, #5B8CFF, #7C5CFF);
                color: white;
                border-radius: 999px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: 850;
            }}

            .calendar-table-events {{
                display: flex;
                flex-direction: column;
                gap: 6px;
            }}

            .calendar-table-event {{
                background: rgba(91, 140, 255, 0.13);
                border: 1px solid rgba(91, 140, 255, 0.18);
                border-radius: 12px;
                padding: 7px 8px;
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


def _render_calendar(year, month, actions):
    calendar_html = _build_calendar_html(year, month, actions)

    components.html(
        calendar_html,
        height=790,
        scrolling=False,
    )


def _render_today_actions(actions):
    today = date.today()

    today_actions = []

    for action in actions:
        action_date = _parse_date(action.get("next_action_date"))

        if action_date == today:
            today_actions.append(action)

    render_section_title("오늘 상담 예정")

    if not today_actions:
        st.info("오늘 예정된 상담이 없습니다.")
        return

    for action in today_actions:
        customer_name = _safe_html(action.get("customer_name"))
        customer_phone = _safe_html(action.get("customer_phone"))
        next_action = _safe_html(action.get("next_action"), "상담 예정")
        owner_name = _safe_html(action.get("owner_name"))

        st.markdown(
            f"""
            <div class="today-action-card">
                <div>
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


def _render_upcoming_actions(actions):
    today = date.today()

    upcoming = []

    for action in actions:
        action_date = _parse_date(action.get("next_action_date"))

        if action_date and action_date >= today:
            upcoming.append(
                {
                    "date": action_date,
                    "action": action,
                }
            )

    upcoming = sorted(upcoming, key=lambda item: item["date"])[:6]

    render_section_title("다가오는 일정")

    if not upcoming:
        st.info("다가오는 상담 일정이 없습니다.")
        return

    for item in upcoming:
        action = item["action"]
        action_date = item["date"]

        customer_name = _safe_html(action.get("customer_name"))
        customer_phone = _safe_html(action.get("customer_phone"))
        next_action = _safe_html(action.get("next_action"), "상담 예정")

        st.markdown(
            f"""
            <div class="upcoming-card">
                <div class="upcoming-date">
                    <div class="upcoming-day">{action_date.day}</div>
                    <div class="upcoming-month">{action_date.month}월</div>
                </div>
                <div class="upcoming-body">
                    <div class="upcoming-title">{customer_name}</div>
                    <div class="upcoming-meta">{customer_phone}</div>
                    <div class="upcoming-desc">{next_action}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _quick_button(label, page):
    if st.button(label, use_container_width=True):
        st.switch_page(page)


def _render_quick_menu():
    render_section_title("빠른 이동")

    _quick_button("고객 등록", "pages/2_고객등록.py")
    _quick_button("고객 리스트", "pages/3_고객리스트.py")
    _quick_button("상담 이력", "pages/4_상담이력.py")


def home_page(user):
    inject_global_css()

    customers = get_customers(user)

    total_customers = len(customers)
    scheduled_customers = _count_by_status(customers, "예정")
    pending_customers = _count_by_status(customers, "보류")
    active_customers = _count_by_status(customers, "진행")

    render_page_header(
        "상담 일정 Dashboard",
        f"{user.get('name', '사용자')}님, 오늘의 일정과 고객 상담 흐름을 확인하세요.",
    )

    year, month = _render_month_selector()

    actions = get_month_next_actions(user, year, month)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_metric_card(
            label="전체 고객",
            value=total_customers,
            desc="등록된 고객 수",
        )

    with col2:
        render_metric_card(
            label="이번 달 상담",
            value=len(actions),
            desc="다음 연락일 기준",
        )

    with col3:
        render_metric_card(
            label="상담 예정",
            value=scheduled_customers,
            desc="상태에 '예정' 포함",
        )

    with col4:
        render_metric_card(
            label="진행 고객",
            value=active_customers,
            desc="상태에 '진행' 포함",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    left, right = st.columns([1.58, 0.82])

    with left:
        _render_calendar(year, month, actions)

    with right:
        st.markdown(
            """
            <div class="crm-card">
            """,
            unsafe_allow_html=True,
        )

        _render_today_actions(actions)

        st.markdown("<br>", unsafe_allow_html=True)

        _render_upcoming_actions(actions)

        st.markdown("<br>", unsafe_allow_html=True)

        _render_quick_menu()

        st.markdown(
            """
            </div>
            """,
            unsafe_allow_html=True,
        )