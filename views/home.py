import calendar
import html
from collections import defaultdict
from datetime import date, datetime

import streamlit as st
import streamlit.components.v1 as components

from utils.ui import (
    inject_global_css,
    render_metric_card,
    render_section_title,
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
        before_date = st.session_state.get("selected_calendar_date")

        if before_date != query_date.isoformat():
            st.session_state.editing_general_schedule_id = None

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
            f'<div class="home-month-title">{st.session_state.calendar_year}년 {st.session_state.calendar_month}월</div>',
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


def _collect_upcoming_items(customer_actions, general_schedules):
    today = date.today()
    items = []

    for action in customer_actions:
        action_date = _parse_date(action.get("next_action_date"))

        if action_date and action_date >= today:
            items.append({
                "date": action_date,
                "type": "고객",
                "title": _safe_text(action.get("customer_name"), "고객명 없음"),
                "desc": _safe_text(action.get("next_action"), "상담 예정"),
            })

    for schedule in general_schedules:
        schedule_date = _parse_date(schedule.get("schedule_date"))

        if schedule_date and schedule_date >= today:
            items.append({
                "date": schedule_date,
                "type": "일반",
                "title": _safe_text(schedule.get("title"), "일반일정"),
                "desc": _safe_text(schedule.get("content"), ""),
            })

    items = sorted(items, key=lambda item: item["date"])

    return items[:4]


def _build_upcoming_board_html(customer_actions, general_schedules):
    upcoming_items = _collect_upcoming_items(customer_actions, general_schedules)

    if not upcoming_items:
        item_html = """
        <div class="upcoming-empty">
            다가오는 일정이 없습니다.
        </div>
        """
    else:
        item_parts = []

        for item in upcoming_items:
            item_date = item["date"]
            item_type = html.escape(item["type"])
            item_title = html.escape(item["title"])
            item_desc = html.escape(item["desc"])

            type_class = "customer"

            if item["type"] == "일반":
                type_class = "general"

            desc_html = ""

            if item_desc:
                desc_html = f'<div class="upcoming-desc">{item_desc}</div>'

            item_parts.append(
                f"""
                <div class="upcoming-item">
                    <div class="upcoming-date">
                        <div class="upcoming-day">{item_date.day}</div>
                        <div class="upcoming-month">{item_date.month}월</div>
                    </div>
                    <div class="upcoming-body">
                        <div class="upcoming-top">
                            <span class="upcoming-type {type_class}">{item_type}</span>
                            <span class="upcoming-title">{item_title}</span>
                        </div>
                        {desc_html}
                    </div>
                </div>
                """
            )

        item_html = "".join(item_parts)

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

            .upcoming-board {{
                width: 100%;
                min-height: 150px;
                background: rgba(15, 23, 42, 0.62);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 24px;
                padding: 24px 28px;
                box-shadow: 0 18px 60px rgba(0, 0, 0, 0.22);
            }}

            .upcoming-board-title {{
                color: #F8FAFC;
                text-align: center;
                font-size: 34px;
                line-height: 1.1;
                font-weight: 850;
                letter-spacing: -0.06em;
                margin-bottom: 18px;
            }}

            .upcoming-content {{
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 12px;
            }}

            .upcoming-empty {{
                color: #94A3B8;
                text-align: center;
                grid-column: 1 / -1;
                padding: 16px;
                font-size: 16px;
            }}

            .upcoming-item {{
                display: flex;
                align-items: center;
                gap: 12px;
                background: rgba(255, 255, 255, 0.055);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 18px;
                padding: 13px;
                min-width: 0;
            }}

            .upcoming-date {{
                width: 48px;
                height: 48px;
                border-radius: 16px;
                background: linear-gradient(135deg, rgba(91, 140, 255, 0.28), rgba(124, 92, 255, 0.18));
                border: 1px solid rgba(255, 255, 255, 0.10);
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
            }}

            .upcoming-day {{
                color: #F8FAFC;
                font-size: 18px;
                font-weight: 900;
                line-height: 1;
            }}

            .upcoming-month {{
                color: #CBD5E1;
                font-size: 11px;
                margin-top: 3px;
            }}

            .upcoming-body {{
                min-width: 0;
            }}

            .upcoming-top {{
                display: flex;
                gap: 6px;
                align-items: center;
                margin-bottom: 4px;
                min-width: 0;
            }}

            .upcoming-type {{
                display: inline-block;
                border-radius: 999px;
                padding: 3px 7px;
                font-size: 10px;
                font-weight: 900;
                flex-shrink: 0;
            }}

            .upcoming-type.customer {{
                color: #BFDBFE;
                background: rgba(59, 130, 246, 0.20);
            }}

            .upcoming-type.general {{
                color: #BBF7D0;
                background: rgba(34, 197, 94, 0.20);
            }}

            .upcoming-title {{
                color: #F8FAFC;
                font-size: 14px;
                font-weight: 850;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }}

            .upcoming-desc {{
                color: #94A3B8;
                font-size: 12px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }}

            @media screen and (max-width: 1000px) {{
                .upcoming-content {{
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                }}
            }}

            @media screen and (max-width: 640px) {{
                .upcoming-content {{
                    grid-template-columns: 1fr;
                }}

                .upcoming-board-title {{
                    font-size: 28px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="upcoming-board">
            <div class="upcoming-board-title">다가오는 일정</div>
            <div class="upcoming-content">
                {item_html}
            </div>
        </div>
    </body>
    </html>
    """


def _render_upcoming_board(customer_actions, general_schedules):
    upcoming_html = _build_upcoming_board_html(
        customer_actions,
        general_schedules,
    )

    components.html(
        upcoming_html,
        height=210,
        scrolling=False,
    )


def _render_calendar_event_chip(event_type, title, desc=""):
    safe_type = _safe_html(event_type)
    safe_title = _safe_html(title)
    safe_desc = _safe_html(desc, "")

    if event_type == "고객":
        bg = "rgba(59, 130, 246, 0.16)"
        border = "rgba(96, 165, 250, 0.30)"
    else:
        bg = "rgba(34, 197, 94, 0.15)"
        border = "rgba(74, 222, 128, 0.28)"

    desc_html = ""

    if safe_desc:
        desc_html = (
            f'<div style="color:#CBD5E1;font-size:10px;'
            f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'
            f'{safe_desc}</div>'
        )

    st.markdown(
        (
            f'<div style="background:{bg};border:1px solid {border};'
            f'border-radius:12px;padding:5px 7px;margin-top:5px;">'
            f'<div style="display:inline-block;color:#F8FAFC;'
            f'background:rgba(255,255,255,0.13);border-radius:999px;'
            f'padding:2px 6px;font-size:9px;font-weight:900;margin-bottom:2px;">'
            f'{safe_type}</div>'
            f'<div style="color:#F8FAFC;font-size:11px;font-weight:800;'
            f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'
            f'{safe_title}</div>'
            f'{desc_html}'
            f'</div>'
        ),
        unsafe_allow_html=True,
    )


def _render_calendar_day_cell(
    year,
    month,
    day,
    selected_date,
    today,
    customer_grouped,
    general_grouped,
):
    current_date = date(year, month, day)

    day_customer_actions = customer_grouped.get(day, [])
    day_general_schedules = general_grouped.get(day, [])

    is_selected = selected_date == current_date
    is_today = today == current_date

    label_parts = [f"{day}"]

    if is_today:
        label_parts.append("오늘")

    if is_selected:
        label_parts.append("선택")

    count_parts = []

    if day_customer_actions:
        count_parts.append(f"고객 {len(day_customer_actions)}")

    if day_general_schedules:
        count_parts.append(f"일반 {len(day_general_schedules)}")

    if count_parts:
        label_parts.append(" / ".join(count_parts))

    button_label = " · ".join(label_parts)

    if st.button(
        button_label,
        key=f"calendar_native_day_{year}_{month}_{day}",
        use_container_width=True,
    ):
        _set_selected_date(current_date)
        st.rerun()

    for action in day_customer_actions[:2]:
        _render_calendar_event_chip(
            "고객",
            action.get("customer_name"),
            action.get("next_action"),
        )

    for schedule in day_general_schedules[:2]:
        _render_calendar_event_chip(
            "일반",
            schedule.get("title"),
            "",
        )

    total_count = len(day_customer_actions) + len(day_general_schedules)
    shown_count = min(len(day_customer_actions), 2) + min(len(day_general_schedules), 2)

    if total_count > shown_count:
        st.caption(f"+{total_count - shown_count}건 더 있음")


def _render_calendar(year, month, customer_actions, general_schedules):
    customer_grouped = _group_customer_actions_by_day(customer_actions)
    general_grouped = _group_general_schedules_by_day(general_schedules)

    selected_date = _get_selected_date()
    today = date.today()

    cal = calendar.Calendar(firstweekday=6)
    weeks = cal.monthdayscalendar(year, month)

    st.markdown(
        """
        <div style="
            background: rgba(15, 23, 42, 0.62);
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 24px;
            padding: 18px;
            box-shadow: 0 18px 60px rgba(0,0,0,0.22);
        ">
        """,
        unsafe_allow_html=True,
    )

    weekday_cols = st.columns(7)

    weekdays = ["일", "월", "화", "수", "목", "금", "토"]

    for index, weekday in enumerate(weekdays):
        with weekday_cols[index]:
            st.markdown(
                f"""
                <div style="
                    color:#CBD5E1;
                    font-size:13px;
                    font-weight:850;
                    text-align:center;
                    padding:8px 0 10px 0;
                ">
                    {weekday}
                </div>
                """,
                unsafe_allow_html=True,
            )

    for week_index, week in enumerate(weeks):
        cols = st.columns(7)

        for day_index, day in enumerate(week):
            with cols[day_index]:
                if day == 0:
                    st.markdown(
                        """
                        <div style="
                            min-height:122px;
                            border-radius:18px;
                            background:rgba(255,255,255,0.025);
                            opacity:0.25;
                            margin-bottom:10px;
                        "></div>
                        """,
                        unsafe_allow_html=True,
                    )
                    continue

                with st.container(border=True):
                    _render_calendar_day_cell(
                        year,
                        month,
                        day,
                        selected_date,
                        today,
                        customer_grouped,
                        general_grouped,
                    )

    st.markdown(
        """
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_schedule_summary_box(selected_customer_actions, selected_general_schedules):
    customer_html = ""

    if selected_customer_actions:
        for action in selected_customer_actions:
            customer_name = _safe_html(action.get("customer_name"), "고객명 없음")
            next_action = _safe_html(action.get("next_action"), "상담 예정")
            customer_phone = _safe_html(action.get("customer_phone"), "연락처 없음")

            customer_html += (
                '<div class="home-schedule-item home-schedule-customer">'
                '<div class="home-schedule-type">고객</div>'
                f'<div class="home-schedule-title">{customer_name}</div>'
                f'<div class="home-schedule-desc">{next_action}</div>'
                f'<div class="home-schedule-meta">{customer_phone}</div>'
                '</div>'
            )
    else:
        customer_html = '<div class="home-schedule-empty">고객일정 없음</div>'

    general_html = ""

    if selected_general_schedules:
        for schedule in selected_general_schedules:
            title = _safe_html(schedule.get("title"), "일반일정")
            content = _safe_html(schedule.get("content"), "")

            content_html = ""

            if content:
                content_html = f'<div class="home-schedule-desc">{content}</div>'

            general_html += (
                '<div class="home-schedule-item home-schedule-general">'
                '<div class="home-schedule-type">일반</div>'
                f'<div class="home-schedule-title">{title}</div>'
                f'{content_html}'
                '</div>'
            )
    else:
        general_html = '<div class="home-schedule-empty">일반일정 없음</div>'

    st.markdown(
        (
            '<div class="home-right-dashed-box">'
            '<div class="home-right-box-title">일정</div>'
            f'<div class="home-schedule-group">{customer_html}</div>'
            f'<div class="home-schedule-group">{general_html}</div>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )


def _render_customer_schedule_buttons(selected_customer_actions):
    if not selected_customer_actions:
        return

    render_section_title("고객일정 수정")

    for action in selected_customer_actions:
        customer_name = _safe_text(action.get("customer_name"), "고객명 없음")

        if st.button(
            f"{customer_name} 상담 이력에서 수정",
            key=f"edit_customer_schedule_{action.get('id')}",
            use_container_width=True,
        ):
            st.session_state.selected_consult_customer_id = action.get("customer_id")
            st.switch_page("pages/4_상담이력.py")


def _render_general_schedule_list(selected_general_schedules):
    if not selected_general_schedules:
        return

    render_section_title("일반일정 관리")

    for schedule in selected_general_schedules:
        title = _safe_text(schedule.get("title"), "일반일정")

        col_edit, col_delete = st.columns(2)

        with col_edit:
            if st.button(
                f"{title} 수정",
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
        form_title = "일반일정 수정"
        default_title = _safe_text(editing_schedule.get("title"), "")
        default_content = _safe_text(editing_schedule.get("content"), "")
        default_date = _parse_date(editing_schedule.get("schedule_date")) or selected_date
        button_label = "수정 저장"
        form_key = f"general_schedule_edit_form_{editing_id}"
        show_cancel = True
    else:
        form_title = "일반일정 입력 / 저장"
        default_title = ""
        default_content = ""
        default_date = selected_date
        button_label = "저장"
        form_key = f"general_schedule_add_form_{selected_date.isoformat()}"
        show_cancel = False

    st.markdown(
        f'<div class="home-right-form-title">{form_title}</div>',
        unsafe_allow_html=True,
    )

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
            height=110,
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
                    "취소",
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
                        _set_selected_date(schedule_date)
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
                    _set_selected_date(schedule_date)
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

    st.markdown(
        (
            '<div class="home-date-label">날짜</div>'
            f'<div class="home-selected-date">{selected_date.year}년 {selected_date.month}월 {selected_date.day}일</div>'
        ),
        unsafe_allow_html=True,
    )

    _render_schedule_summary_box(
        selected_customer_actions,
        selected_general_schedules,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    _render_customer_schedule_buttons(selected_customer_actions)

    _render_general_schedule_list(selected_general_schedules)

    st.markdown("<br>", unsafe_allow_html=True)

    _render_general_schedule_form(
        user,
        selected_date,
        selected_general_schedules,
    )


def home_page(user):
    inject_global_css()

    _init_calendar_state()

    customers = get_customers(user)

    total_customers = len(customers)
    active_customers = _count_by_status(customers, "진행")

    year, month = _render_month_selector()

    customer_actions = get_month_next_actions(user, year, month)
    general_schedules = get_month_general_schedules(user, year, month)

    _render_upcoming_board(customer_actions, general_schedules)

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
            desc="상담 이력 기준",
        )

    with col3:
        render_metric_card(
            label="일반일정",
            value=len(general_schedules),
            desc="직접 등록 일정",
        )

    with col4:
        render_metric_card(
            label="진행 고객",
            value=active_customers,
            desc="진행 상태 고객",
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