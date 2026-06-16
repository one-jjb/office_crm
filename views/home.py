import calendar
import html
from collections import defaultdict
from datetime import date, datetime

import streamlit as st

from utils.ui import render_metric_card, render_section_title
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

    return value if value else default


def _safe_html(value, default="-"):
    return html.escape(_safe_text(value, default))


def _parse_date(value):
    if not value:
        return None

    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def _init_calendar_state():
    today = date.today()

    st.session_state.setdefault("calendar_year", today.year)
    st.session_state.setdefault("calendar_month", today.month)
    st.session_state.setdefault("selected_calendar_date", today.isoformat())
    st.session_state.setdefault("editing_general_schedule_id", None)


def _get_selected_date():
    return _parse_date(st.session_state.get("selected_calendar_date")) or date.today()


def _set_selected_date(selected_date):
    st.session_state.selected_calendar_date = selected_date.isoformat()
    st.session_state.calendar_year = selected_date.year
    st.session_state.calendar_month = selected_date.month
    st.session_state.editing_general_schedule_id = None


def _group_by_day(items, date_key):
    grouped = defaultdict(list)

    for item in items:
        item_date = _parse_date(item.get(date_key))

        if item_date:
            grouped[item_date.day].append(item)

    return grouped


def _items_for_date(items, date_key, target_date):
    result = []

    for item in items:
        item_date = _parse_date(item.get(date_key))

        if item_date == target_date:
            result.append(item)

    return result


def _count_by_status(customers, keyword):
    return sum(1 for customer in customers if keyword in str(customer.get("status", "")))


def _render_month_selector():
    left, center, right = st.columns([0.18, 0.64, 0.18])

    with left:
        if st.button("◀ 이전달", use_container_width=True, key="calendar_prev_month"):
            if st.session_state.calendar_month == 1:
                st.session_state.calendar_year -= 1
                st.session_state.calendar_month = 12
            else:
                st.session_state.calendar_month -= 1

            _set_selected_date(date(st.session_state.calendar_year, st.session_state.calendar_month, 1))
            st.rerun()

    with center:
        st.markdown(
            f'<div class="home-month-title">{st.session_state.calendar_year}년 {st.session_state.calendar_month}월</div>',
            unsafe_allow_html=True,
        )

    with right:
        if st.button("다음달 ▶", use_container_width=True, key="calendar_next_month"):
            if st.session_state.calendar_month == 12:
                st.session_state.calendar_year += 1
                st.session_state.calendar_month = 1
            else:
                st.session_state.calendar_month += 1

            _set_selected_date(date(st.session_state.calendar_year, st.session_state.calendar_month, 1))
            st.rerun()

    return st.session_state.calendar_year, st.session_state.calendar_month


def _get_upcoming_items(customer_actions, general_schedules):
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

    return sorted(items, key=lambda item: item["date"])[:4]


def _render_upcoming_board(customer_actions, general_schedules):
    items = _get_upcoming_items(customer_actions, general_schedules)

    if not items:
        body = '<div class="home-upcoming-empty">다가오는 일정이 없습니다.</div>'
    else:
        parts = []

        for item in items:
            item_type = _safe_html(item["type"])
            item_title = _safe_html(item["title"])
            item_desc = _safe_html(item["desc"], "")
            chip_class = "home-chip-customer" if item["type"] == "고객" else "home-chip-general"

            desc_html = ""
            if item_desc:
                desc_html = f'<div class="home-upcoming-desc">{item_desc}</div>'

            parts.append(
                '<div class="home-upcoming-item">'
                '<div class="home-upcoming-date">'
                f'<div class="home-upcoming-day">{item["date"].day}</div>'
                f'<div class="home-upcoming-month">{item["date"].month}월</div>'
                '</div>'
                '<div class="home-upcoming-body">'
                '<div class="home-upcoming-top">'
                f'<span class="home-chip-type {chip_class}">{item_type}</span>'
                f'<span class="home-upcoming-name">{item_title}</span>'
                '</div>'
                f'{desc_html}'
                '</div>'
                '</div>'
            )

        body = "".join(parts)

    st.markdown(
        (
            '<div class="home-upcoming-board">'
            '<div class="home-upcoming-title">다가오는 일정</div>'
            f'<div class="home-upcoming-grid">{body}</div>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )


def _render_calendar_chip(event_type, title, desc=""):
    chip_class = "customer" if event_type == "고객" else "general"
    type_class = "home-chip-customer" if event_type == "고객" else "home-chip-general"

    desc_html = ""
    safe_desc = _safe_html(desc, "")

    if safe_desc:
        desc_html = f'<div class="home-calendar-event-desc">{safe_desc}</div>'

    st.markdown(
        (
            f'<div class="home-calendar-event {chip_class}">'
            f'<span class="home-chip-type {type_class}">{_safe_html(event_type)}</span>'
            f'<div class="home-calendar-event-title">{_safe_html(title)}</div>'
            f'{desc_html}'
            '</div>'
        ),
        unsafe_allow_html=True,
    )


def _day_button_label(day, is_today, is_selected, customer_count, general_count):
    parts = [str(day)]

    if is_today:
        parts.append("오늘")

    if is_selected:
        parts.append("선택")

    counts = []

    if customer_count:
        counts.append(f"고객 {customer_count}")

    if general_count:
        counts.append(f"일반 {general_count}")

    if counts:
        parts.append(" / ".join(counts))

    return " · ".join(parts)


def _render_day_cell(year, month, day, selected_date, customer_grouped, general_grouped):
    current_date = date(year, month, day)
    today = date.today()

    customer_items = customer_grouped.get(day, [])
    general_items = general_grouped.get(day, [])

    label = _day_button_label(
        day=day,
        is_today=current_date == today,
        is_selected=current_date == selected_date,
        customer_count=len(customer_items),
        general_count=len(general_items),
    )

    if st.button(label, key=f"calendar_day_{year}_{month}_{day}", use_container_width=True):
        _set_selected_date(current_date)
        st.rerun()

    for action in customer_items[:2]:
        _render_calendar_chip("고객", action.get("customer_name"), action.get("next_action"))

    for schedule in general_items[:2]:
        _render_calendar_chip("일반", schedule.get("title"))

    hidden_count = len(customer_items) + len(general_items) - min(len(customer_items), 2) - min(len(general_items), 2)

    if hidden_count > 0:
        st.caption(f"+{hidden_count}건 더 있음")


def _render_calendar(year, month, customer_actions, general_schedules):
    selected_date = _get_selected_date()
    customer_grouped = _group_by_day(customer_actions, "next_action_date")
    general_grouped = _group_by_day(general_schedules, "schedule_date")

    st.markdown('<div class="home-calendar-shell">', unsafe_allow_html=True)

    for col, weekday in zip(st.columns(7), ["일", "월", "화", "수", "목", "금", "토"]):
        with col:
            st.markdown(f'<div class="home-weekday">{weekday}</div>', unsafe_allow_html=True)

    for week in calendar.Calendar(firstweekday=6).monthdayscalendar(year, month):
        cols = st.columns(7)

        for col, day in zip(cols, week):
            with col:
                if day == 0:
                    st.markdown('<div class="home-empty-day"></div>', unsafe_allow_html=True)
                else:
                    with st.container(border=True):
                        _render_day_cell(
                            year=year,
                            month=month,
                            day=day,
                            selected_date=selected_date,
                            customer_grouped=customer_grouped,
                            general_grouped=general_grouped,
                        )

    st.markdown("</div>", unsafe_allow_html=True)


def _schedule_card(schedule_type, title, desc="", meta=""):
    card_class = "home-schedule-customer" if schedule_type == "고객" else "home-schedule-general"
    chip_class = "home-chip-customer" if schedule_type == "고객" else "home-chip-general"

    desc_html = f'<div class="home-schedule-desc">{_safe_html(desc)}</div>' if desc else ""
    meta_html = f'<div class="home-schedule-meta">{_safe_html(meta)}</div>' if meta else ""

    return (
        f'<div class="home-schedule-item {card_class}">'
        f'<span class="home-chip-type {chip_class}">{_safe_html(schedule_type)}</span>'
        f'<div class="home-schedule-title">{_safe_html(title)}</div>'
        f'{desc_html}'
        f'{meta_html}'
        '</div>'
    )


def _render_schedule_summary(customer_items, general_items):
    if customer_items:
        customer_html = "".join(
            _schedule_card(
                "고객",
                action.get("customer_name"),
                action.get("next_action"),
                action.get("customer_phone"),
            )
            for action in customer_items
        )
    else:
        customer_html = '<div class="home-schedule-empty">고객일정 없음</div>'

    if general_items:
        general_html = "".join(
            _schedule_card(
                "일반",
                schedule.get("title"),
                schedule.get("content"),
            )
            for schedule in general_items
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


def _render_customer_edit_buttons(customer_items):
    if not customer_items:
        return

    render_section_title("고객일정 수정")

    for action in customer_items:
        customer_name = _safe_text(action.get("customer_name"), "고객명 없음")

        if st.button(
            f"{customer_name} 상담 이력에서 수정",
            key=f"edit_customer_schedule_{action.get('id')}",
            use_container_width=True,
        ):
            st.session_state.selected_consult_customer_id = action.get("customer_id")
            st.switch_page("pages/4_상담이력.py")


def _find_schedule(schedules, schedule_id):
    for schedule in schedules:
        if schedule.get("id") == schedule_id:
            return schedule

    return None


def _render_general_schedule_buttons(general_items):
    if not general_items:
        return

    render_section_title("일반일정 관리")

    for schedule in general_items:
        title = _safe_text(schedule.get("title"), "일반일정")
        col_edit, col_delete = st.columns(2)

        with col_edit:
            if st.button(f"{title} 수정", key=f"edit_general_{schedule.get('id')}", use_container_width=True):
                st.session_state.editing_general_schedule_id = schedule.get("id")
                st.rerun()

        with col_delete:
            if st.button("삭제", key=f"delete_general_{schedule.get('id')}", use_container_width=True):
                deleted = delete_general_schedule(schedule.get("id"), st.session_state.user)

                if deleted:
                    st.success("일반일정이 삭제되었습니다.")
                    st.session_state.editing_general_schedule_id = None
                    st.rerun()
                else:
                    st.error("삭제 권한이 없거나 일정을 찾을 수 없습니다.")


def _render_general_schedule_form(user, selected_date, general_items):
    editing_id = st.session_state.get("editing_general_schedule_id")
    editing_schedule = _find_schedule(general_items, editing_id) if editing_id else None

    form_title = "일반일정 수정" if editing_schedule else "일반일정 입력 / 저장"
    button_label = "수정 저장" if editing_schedule else "저장"
    form_key = f"general_schedule_form_{editing_id or selected_date.isoformat()}"

    default_date = selected_date
    default_title = ""
    default_content = ""

    if editing_schedule:
        default_date = _parse_date(editing_schedule.get("schedule_date")) or selected_date
        default_title = _safe_text(editing_schedule.get("title"), "")
        default_content = _safe_text(editing_schedule.get("content"), "")

    st.markdown(f'<div class="home-right-form-title">{form_title}</div>', unsafe_allow_html=True)

    with st.form(form_key):
        schedule_date = st.date_input("일정 날짜", value=default_date, key=f"{form_key}_date")
        title = st.text_input("일정 제목", value=default_title, placeholder="예: 지점 회의, 고객자료 정리", key=f"{form_key}_title")
        content = st.text_area("일정 내용", value=default_content, placeholder="일정 상세 내용을 입력하세요.", height=110, key=f"{form_key}_content")

        if editing_schedule:
            col_save, col_cancel = st.columns(2)

            with col_save:
                submitted = st.form_submit_button(button_label, use_container_width=True)

            with col_cancel:
                cancel = st.form_submit_button("취소", use_container_width=True)
        else:
            submitted = st.form_submit_button(button_label, use_container_width=True)
            cancel = False

        if submitted:
            if not title.strip():
                st.warning("일정 제목을 입력하세요.")
                return

            if editing_schedule:
                ok = update_general_schedule(
                    schedule_id=editing_id,
                    user=user,
                    schedule_date=str(schedule_date),
                    title=title.strip(),
                    content=content.strip(),
                )

                if not ok:
                    st.error("수정 권한이 없거나 일정을 찾을 수 없습니다.")
                    return

                st.success("일반일정이 수정되었습니다.")
            else:
                add_general_schedule(
                    user_id=user["id"],
                    schedule_date=str(schedule_date),
                    title=title.strip(),
                    content=content.strip(),
                )

                st.success("일반일정이 추가되었습니다.")

            st.session_state.editing_general_schedule_id = None
            _set_selected_date(schedule_date)
            st.rerun()

        if cancel:
            st.session_state.editing_general_schedule_id = None
            st.rerun()


def _render_selected_day_panel(user, customer_actions, general_schedules):
    selected_date = _get_selected_date()

    customer_items = _items_for_date(customer_actions, "next_action_date", selected_date)
    general_items = _items_for_date(general_schedules, "schedule_date", selected_date)

    st.markdown(
        (
            '<div class="home-date-label">날짜</div>'
            f'<div class="home-selected-date">{selected_date.year}년 {selected_date.month}월 {selected_date.day}일</div>'
        ),
        unsafe_allow_html=True,
    )

    _render_schedule_summary(customer_items, general_items)
    _render_customer_edit_buttons(customer_items)
    _render_general_schedule_buttons(general_items)
    st.markdown("<br>", unsafe_allow_html=True)
    _render_general_schedule_form(user, selected_date, general_items)


def home_page(user):
    _init_calendar_state()

    customers = get_customers(user)
    year, month = _render_month_selector()

    customer_actions = get_month_next_actions(user, year, month)
    general_schedules = get_month_general_schedules(user, year, month)

    _render_upcoming_board(customer_actions, general_schedules)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_metric_card("전체 고객", len(customers), "등록된 고객 수")

    with col2:
        render_metric_card("고객일정", len(customer_actions), "상담 이력 기준")

    with col3:
        render_metric_card("일반일정", len(general_schedules), "직접 등록 일정")

    with col4:
        render_metric_card("진행 고객", _count_by_status(customers, "진행"), "진행 상태 고객")

    st.markdown("<br>", unsafe_allow_html=True)

    left, right = st.columns([1.45, 0.95])

    with left:
        _render_calendar(year, month, customer_actions, general_schedules)

    with right:
        _render_selected_day_panel(user, customer_actions, general_schedules)