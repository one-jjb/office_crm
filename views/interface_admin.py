from collections import defaultdict

import streamlit as st

from utils.ui import render_page_header, render_section_title
from utils.ui_config import (
    get_ui_settings_rows,
    update_many_ui_settings,
    reset_ui_settings_to_defaults,
)


def _as_bool(value):
    return str(value).strip().lower() in [
        "true",
        "1",
        "yes",
        "y",
        "on",
    ]


def _safe_color(value, default="#5B8CFF"):
    value = str(value or "").strip()

    if value.startswith("#") and len(value) == 7:
        return value

    return default


def _render_input(row):
    setting_key = row["setting_key"]
    label = row["label"]
    value = row.get("value") or row.get("default_value") or ""
    input_type = row["input_type"]
    description = row.get("description") or ""

    widget_key = f"ui_setting_{setting_key}"

    if input_type == "color":
        return st.color_picker(
            label=label,
            value=_safe_color(value),
            key=widget_key,
            help=description,
        )

    if input_type == "number":
        try:
            number_value = int(float(value))
        except Exception:
            number_value = 0

        return st.number_input(
            label=label,
            min_value=0,
            max_value=999,
            value=number_value,
            step=1,
            key=widget_key,
            help=description,
        )

    if input_type == "toggle":
        checked = st.toggle(
            label=label,
            value=_as_bool(value),
            key=widget_key,
            help=description,
        )

        return "true" if checked else "false"

    return st.text_input(
        label=label,
        value=str(value),
        key=widget_key,
        help=description,
    )


def _group_rows(rows):
    grouped = defaultdict(list)

    for row in rows:
        grouped[row["group_name"]].append(row)

    group_order = [
        "색상 설정",
        "메인 화면 문구",
        "KPI 문구",
        "표시 설정",
        "화면 옵션",
    ]

    ordered_groups = []

    for group_name in group_order:
        if group_name in grouped:
            ordered_groups.append((group_name, grouped[group_name]))

    for group_name, group_items in grouped.items():
        if group_name not in group_order:
            ordered_groups.append((group_name, group_items))

    return ordered_groups


def interface_admin_page(user):
    render_page_header(
        "인터페이스 관리",
        "메인 화면의 색상, 문구, 표시 여부, 표시 개수를 관리자 페이지에서 설정합니다.",
    )

    st.info(
        "설정을 저장한 뒤 메인 화면으로 이동하거나 새로고침하면 변경된 인터페이스가 적용됩니다."
    )

    rows = get_ui_settings_rows()
    grouped_rows = _group_rows(rows)

    updates = {}

    with st.form("interface_settings_form"):
        for group_name, group_items in grouped_rows:
            render_section_title(group_name)

            for row in group_items:
                updates[row["setting_key"]] = _render_input(row)

            st.markdown("---")

        submitted = st.form_submit_button(
            "인터페이스 설정 저장",
            use_container_width=True,
        )

        if submitted:
            update_many_ui_settings(updates)
            st.success("인터페이스 설정이 저장되었습니다.")
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    col_reset, col_desc = st.columns([0.25, 0.75])

    with col_reset:
        if st.button(
            "기본값으로 초기화",
            use_container_width=True,
            key="reset_ui_settings_button",
        ):
            reset_ui_settings_to_defaults()
            st.success("기본값으로 초기화되었습니다.")
            st.rerun()

    with col_desc:
        st.caption(
            "초기화하면 색상, 문구, 표시 설정, 표시 개수가 모두 기본값으로 돌아갑니다."
        )