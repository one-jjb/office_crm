import html

import streamlit as st


def inject_global_css():
    st.markdown(
        """
        <style>

        /* ======================================================
           기본 숨김
        ====================================================== */

        #MainMenu {
            visibility: hidden;
        }

        footer {
            visibility: hidden;
        }

        header {
            visibility: hidden;
        }

        /* ======================================================
           전체 레이아웃
        ====================================================== */

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(91, 140, 255, 0.18), transparent 34%),
                radial-gradient(circle at top right, rgba(124, 92, 255, 0.16), transparent 32%),
                linear-gradient(135deg, #0F172A, #111827, #1E293B);
            color: #F8FAFC;
        }

        .block-container {
            padding-top: 2.1rem;
            padding-bottom: 2.4rem;
            max-width: 1440px;
        }

        /* ======================================================
           사이드바
        ====================================================== */

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #020617, #0F172A);
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }

        [data-testid="stSidebar"] * {
            color: #F8FAFC !important;
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            color: #CBD5E1 !important;
        }

        [data-testid="stSidebarNav"] {
            display: none;
        }

        /* ======================================================
           텍스트
        ====================================================== */

        h1, h2, h3 {
            color: #F8FAFC;
            letter-spacing: -0.04em;
        }

        p, span, label {
            color: #E2E8F0;
        }

        .crm-title {
            font-size: 42px;
            line-height: 1.15;
            font-weight: 850;
            color: #F8FAFC;
            letter-spacing: -1.4px;
            margin-bottom: 8px;
        }

        .crm-subtitle {
            font-size: 16px;
            color: #94A3B8;
            margin-bottom: 22px;
        }

        .crm-section-title {
            font-size: 20px;
            font-weight: 800;
            color: #F8FAFC;
            margin-bottom: 14px;
            letter-spacing: -0.04em;
        }

        .crm-muted {
            color: #94A3B8;
            font-size: 14px;
        }

        /* ======================================================
           카드 공통
        ====================================================== */

        .crm-card {
            background: rgba(15, 23, 42, 0.62);
            border: 1px solid rgba(255, 255, 255, 0.10);
            border-radius: 24px;
            padding: 24px;
            backdrop-filter: blur(18px);
            box-shadow: 0 18px 60px rgba(0, 0, 0, 0.22);
            margin-bottom: 18px;
        }

        .crm-card-compact {
            background: rgba(15, 23, 42, 0.58);
            border: 1px solid rgba(255, 255, 255, 0.09);
            border-radius: 20px;
            padding: 18px;
            backdrop-filter: blur(18px);
            box-shadow: 0 12px 38px rgba(0, 0, 0, 0.16);
            margin-bottom: 14px;
        }

        .crm-hero {
            background:
                linear-gradient(135deg, rgba(91, 140, 255, 0.22), rgba(124, 92, 255, 0.12)),
                rgba(15, 23, 42, 0.64);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 28px;
            padding: 28px;
            box-shadow: 0 18px 70px rgba(0, 0, 0, 0.28);
            margin-bottom: 22px;
        }

        .crm-hero-title {
            color: #F8FAFC;
            font-size: 30px;
            font-weight: 850;
            letter-spacing: -0.06em;
            margin-bottom: 8px;
        }

        .crm-hero-sub {
            color: #CBD5E1;
            font-size: 15px;
            line-height: 1.65;
        }

        /* ======================================================
           KPI 카드
        ====================================================== */

        .metric-card {
            background:
                linear-gradient(135deg, rgba(91, 140, 255, 0.18), rgba(124, 92, 255, 0.08)),
                rgba(15, 23, 42, 0.66);
            border: 1px solid rgba(255, 255, 255, 0.10);
            border-radius: 22px;
            padding: 21px 22px;
            backdrop-filter: blur(18px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.18);
            min-height: 124px;
        }

        .metric-label {
            color: #CBD5E1;
            font-size: 14px;
            font-weight: 650;
            margin-bottom: 10px;
        }

        .metric-value {
            color: #FFFFFF;
            font-size: 34px;
            line-height: 1;
            font-weight: 850;
            letter-spacing: -0.05em;
            margin-bottom: 8px;
        }

        .metric-desc {
            color: #94A3B8;
            font-size: 13px;
        }

        /* ======================================================
           최근 고객 카드
        ====================================================== */

        .recent-customer-card {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 18px;
            background: rgba(255, 255, 255, 0.055);
            border: 1px solid rgba(255, 255, 255, 0.10);
            border-radius: 20px;
            padding: 17px 18px;
            margin-bottom: 12px;
            transition: 0.15s ease;
        }

        .recent-customer-card:hover {
            background: rgba(255, 255, 255, 0.075);
            border-color: rgba(148, 163, 184, 0.24);
            transform: translateY(-1px);
        }

        .recent-customer-left {
            display: flex;
            align-items: center;
            gap: 14px;
            min-width: 0;
        }

        .recent-avatar {
            width: 42px;
            height: 42px;
            border-radius: 15px;
            background: linear-gradient(135deg, #5B8CFF, #7C5CFF);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 850;
            box-shadow: 0 10px 26px rgba(91, 140, 255, 0.20);
            flex-shrink: 0;
        }

        .recent-main {
            min-width: 0;
        }

        .recent-name {
            color: #F8FAFC;
            font-size: 16px;
            font-weight: 800;
            margin-bottom: 4px;
            letter-spacing: -0.03em;
        }

        .recent-meta {
            color: #94A3B8;
            font-size: 13px;
            white-space: nowrap;
        }

        .recent-customer-right {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 7px;
            flex-shrink: 0;
        }

        .recent-sub {
            color: #CBD5E1;
            font-size: 12.5px;
            white-space: nowrap;
        }

        .recent-status {
            border-radius: 999px;
            padding: 5px 10px;
            font-size: 12px;
            font-weight: 800;
            letter-spacing: -0.02em;
            border: 1px solid rgba(255, 255, 255, 0.10);
        }

        .status-active {
            color: #BFDBFE;
            background: rgba(59, 130, 246, 0.18);
            border-color: rgba(96, 165, 250, 0.28);
        }

        .status-done {
            color: #BBF7D0;
            background: rgba(34, 197, 94, 0.16);
            border-color: rgba(74, 222, 128, 0.26);
        }

        .status-pending {
            color: #FDE68A;
            background: rgba(245, 158, 11, 0.16);
            border-color: rgba(251, 191, 36, 0.26);
        }

        .status-scheduled {
            color: #DDD6FE;
            background: rgba(139, 92, 246, 0.16);
            border-color: rgba(167, 139, 250, 0.28);
        }

        .status-default {
            color: #CBD5E1;
            background: rgba(148, 163, 184, 0.13);
            border-color: rgba(148, 163, 184, 0.22);
        }

        /* ======================================================
           빠른 메뉴 카드
        ====================================================== */

        .quick-card {
            background: rgba(255, 255, 255, 0.055);
            border: 1px solid rgba(255, 255, 255, 0.10);
            border-radius: 20px;
            padding: 18px;
            margin-bottom: 12px;
        }

        .quick-title {
            font-size: 16px;
            font-weight: 800;
            color: #F8FAFC;
            margin-bottom: 4px;
        }

        .quick-desc {
            color: #94A3B8;
            font-size: 13px;
            line-height: 1.55;
            margin-bottom: 12px;
        }

        /* ======================================================
           달력 메인 - 월 선택
        ====================================================== */

        .calendar-month-title {
            text-align: center;
            color: #F8FAFC;
            font-size: 28px;
            font-weight: 850;
            letter-spacing: -0.06em;
            padding-top: 6px;
        }

        /* ======================================================
           표 형태 달력
        ====================================================== */

        .calendar-table-wrap {
            padding: 18px;
            overflow-x: auto;
        }

        .calendar-table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 10px;
            table-layout: fixed;
        }

        .calendar-table-weekday {
            color: #CBD5E1;
            font-size: 13px;
            font-weight: 850;
            text-align: center;
            padding: 8px 0 10px 0;
        }

        .calendar-table-cell {
            height: 128px;
            vertical-align: top;
            background: rgba(255, 255, 255, 0.045);
            border: 1px solid rgba(255, 255, 255, 0.085);
            border-radius: 18px;
            padding: 12px;
            overflow: hidden;
            transition: 0.15s ease;
        }

        .calendar-table-cell:hover {
            background: rgba(255, 255, 255, 0.07);
            border-color: rgba(148, 163, 184, 0.24);
            transform: translateY(-1px);
        }

        .calendar-table-empty {
            opacity: 0.22;
            background: rgba(255, 255, 255, 0.025);
        }

        .calendar-table-today {
            border-color: rgba(91, 140, 255, 0.72);
            box-shadow: 0 0 0 1px rgba(91, 140, 255, 0.32);
            background:
                linear-gradient(135deg, rgba(91, 140, 255, 0.13), rgba(124, 92, 255, 0.07)),
                rgba(255, 255, 255, 0.055);
        }

        .calendar-table-day-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 8px;
        }

        .calendar-table-day-number {
            color: #F8FAFC;
            font-size: 15px;
            font-weight: 900;
        }

        .calendar-table-count {
            background: linear-gradient(135deg, #5B8CFF, #7C5CFF);
            color: white;
            border-radius: 999px;
            padding: 2px 8px;
            font-size: 11px;
            font-weight: 850;
        }

        .calendar-table-events {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .calendar-table-event {
            background: rgba(91, 140, 255, 0.13);
            border: 1px solid rgba(91, 140, 255, 0.18);
            border-radius: 12px;
            padding: 7px 8px;
        }

        .calendar-table-event-name {
            color: #F8FAFC;
            font-size: 12px;
            font-weight: 800;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .calendar-table-event-desc {
            color: #CBD5E1;
            font-size: 11px;
            margin-top: 2px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .calendar-table-more {
            color: #94A3B8;
            font-size: 11px;
            padding-left: 4px;
        }

        /* ======================================================
           오늘 상담 / 다가오는 일정
        ====================================================== */

        .today-action-card {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            background: rgba(255, 255, 255, 0.055);
            border: 1px solid rgba(255, 255, 255, 0.10);
            border-radius: 18px;
            padding: 15px;
            margin-bottom: 10px;
        }

        .today-action-title {
            color: #F8FAFC;
            font-size: 15px;
            font-weight: 850;
            margin-bottom: 4px;
        }

        .today-action-meta {
            color: #94A3B8;
            font-size: 12px;
        }

        .today-action-right {
            text-align: right;
            flex-shrink: 0;
        }

        .today-action-badge {
            color: #DDD6FE;
            background: rgba(139, 92, 246, 0.16);
            border: 1px solid rgba(167, 139, 250, 0.28);
            border-radius: 999px;
            padding: 5px 9px;
            font-size: 11px;
            font-weight: 850;
            margin-bottom: 6px;
        }

        .today-action-owner {
            color: #94A3B8;
            font-size: 11px;
        }

        .upcoming-card {
            display: flex;
            gap: 12px;
            align-items: flex-start;
            background: rgba(255, 255, 255, 0.045);
            border: 1px solid rgba(255, 255, 255, 0.085);
            border-radius: 18px;
            padding: 14px;
            margin-bottom: 10px;
        }

        .upcoming-date {
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
        }

        .upcoming-day {
            color: white;
            font-size: 17px;
            font-weight: 900;
            line-height: 1;
        }

        .upcoming-month {
            color: #CBD5E1;
            font-size: 11px;
            margin-top: 3px;
        }

        .upcoming-body {
            min-width: 0;
        }

        .upcoming-title {
            color: #F8FAFC;
            font-size: 14px;
            font-weight: 850;
            margin-bottom: 3px;
        }

        .upcoming-meta {
            color: #94A3B8;
            font-size: 12px;
            margin-bottom: 5px;
        }

        .upcoming-desc {
            color: #CBD5E1;
            font-size: 12px;
            line-height: 1.45;
        }

        /* ======================================================
           버튼
        ====================================================== */

        .stButton > button {
            border: none;
            border-radius: 15px;
            background: linear-gradient(135deg, #5B8CFF, #7C5CFF);
            color: white;
            font-weight: 750;
            min-height: 43px;
            box-shadow: 0 10px 28px rgba(91, 140, 255, 0.18);
            transition: 0.15s ease;
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 14px 34px rgba(91, 140, 255, 0.26);
            border: none;
            color: white;
        }

        .stButton > button:active {
            transform: translateY(0px);
        }

        /* ======================================================
           입력창
        ====================================================== */

        .stTextInput > div > div > input,
        .stTextArea textarea,
        .stSelectbox div[data-baseweb="select"] > div,
        .stDateInput div[data-baseweb="input"] input {
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.10);
            border-radius: 14px;
            color: #F8FAFC;
        }

        .stTextInput > label,
        .stTextArea > label,
        .stSelectbox > label,
        .stDateInput > label {
            color: #CBD5E1 !important;
            font-weight: 650;
        }

        /* ======================================================
           데이터프레임
        ====================================================== */

        [data-testid="stDataFrame"] {
            border-radius: 18px;
            overflow: hidden;
            border: 1px solid rgba(255, 255, 255, 0.09);
            background: rgba(15, 23, 42, 0.42);
        }

        /* ======================================================
           알림
        ====================================================== */

        [data-testid="stAlert"] {
            border-radius: 18px;
            border: 1px solid rgba(255, 255, 255, 0.10);
        }

        hr {
            border-color: rgba(255, 255, 255, 0.10);
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title, subtitle=None):
    safe_title = html.escape(str(title))

    st.markdown(
        f"""
        <div class="crm-title">{safe_title}</div>
        """,
        unsafe_allow_html=True,
    )

    if subtitle:
        safe_subtitle = html.escape(str(subtitle))

        st.markdown(
            f"""
            <div class="crm-subtitle">{safe_subtitle}</div>
            """,
            unsafe_allow_html=True,
        )


def render_metric_card(label, value, desc=""):
    safe_label = html.escape(str(label))
    safe_value = html.escape(str(value))
    safe_desc = html.escape(str(desc))

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{safe_label}</div>
            <div class="metric-value">{safe_value}</div>
            <div class="metric-desc">{safe_desc}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_title(title):
    safe_title = html.escape(str(title))

    st.markdown(
        f"""
        <div class="crm-section-title">{safe_title}</div>
        """,
        unsafe_allow_html=True,
    )