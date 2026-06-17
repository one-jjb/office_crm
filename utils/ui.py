import html

import streamlit as st

from utils.ui_config import get_ui_settings_map


def _hex_to_rgb(hex_color):
    value = str(hex_color or "").strip().replace("#", "")

    if len(value) != 6:
        return None

    try:
        return (
            int(value[0:2], 16),
            int(value[2:4], 16),
            int(value[4:6], 16),
        )
    except Exception:
        return None


def _rgba(hex_color, alpha, fallback):
    rgb = _hex_to_rgb(hex_color)

    if rgb is None:
        return fallback

    return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha})"


def _get_theme_palette(theme_mode):
    if theme_mode == "light":
        return {
            "app_bg": """
                radial-gradient(circle at top left, rgba(91, 140, 255, 0.14), transparent 34%),
                radial-gradient(circle at top right, rgba(124, 92, 255, 0.10), transparent 32%),
                linear-gradient(135deg, #F8FAFC, #EEF2FF, #F1F5F9)
            """,
            "sidebar_bg": "linear-gradient(180deg, #FFFFFF, #F1F5F9)",
            "text_main": "#0F172A",
            "text_sub": "#475569",
            "text_muted": "#64748B",
            "card_bg": "rgba(255, 255, 255, 0.78)",
            "card_bg_soft": "rgba(255, 255, 255, 0.66)",
            "card_border": "rgba(15, 23, 42, 0.10)",
            "card_shadow": "0 18px 60px rgba(15, 23, 42, 0.10)",
            "soft_bg": "rgba(15, 23, 42, 0.035)",
            "soft_hover": "rgba(91, 140, 255, 0.075)",
            "input_bg": "rgba(255, 255, 255, 0.92)",
            "input_border": "rgba(15, 23, 42, 0.12)",
            "table_bg": "rgba(255, 255, 255, 0.70)",
            "dash_border": "rgba(11, 37, 51, 0.50)",
        }

    return {
        "app_bg": """
            radial-gradient(circle at top left, rgba(91, 140, 255, 0.18), transparent 34%),
            radial-gradient(circle at top right, rgba(124, 92, 255, 0.16), transparent 32%),
            linear-gradient(135deg, #0F172A, #111827, #1E293B)
        """,
        "sidebar_bg": "linear-gradient(180deg, #020617, #0F172A)",
        "text_main": "#F8FAFC",
        "text_sub": "#CBD5E1",
        "text_muted": "#94A3B8",
        "card_bg": "rgba(15, 23, 42, 0.62)",
        "card_bg_soft": "rgba(15, 23, 42, 0.58)",
        "card_border": "rgba(255, 255, 255, 0.10)",
        "card_shadow": "0 18px 60px rgba(0, 0, 0, 0.22)",
        "soft_bg": "rgba(255, 255, 255, 0.055)",
        "soft_hover": "rgba(255, 255, 255, 0.075)",
        "input_bg": "rgba(255, 255, 255, 0.06)",
        "input_border": "rgba(255, 255, 255, 0.10)",
        "table_bg": "rgba(15, 23, 42, 0.42)",
        "dash_border": "rgba(11, 37, 51, 0.88)",
    }


def _get_number(settings, key, default):
    try:
        return int(float(settings.get(key, default)))
    except Exception:
        return default


def get_current_theme():
    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "dark"

    return st.session_state.theme_mode


def render_theme_toggle(key="theme_toggle_button"):
    current_theme = get_current_theme()

    if current_theme == "dark":
        label = "화이트 모드"
        next_theme = "light"
    else:
        label = "다크 모드"
        next_theme = "dark"

    if st.button(label, use_container_width=True, key=key):
        st.session_state.theme_mode = next_theme
        st.rerun()


def inject_global_css(theme_mode=None):
    if theme_mode is None:
        theme_mode = get_current_theme()

    palette = _get_theme_palette(theme_mode)
    settings = get_ui_settings_map()

    primary = settings.get("primary_color", "#5B8CFF")
    secondary = settings.get("secondary_color", "#7C5CFF")
    customer = settings.get("customer_color", "#3B82F6")
    general = settings.get("general_color", "#22C55E")

    card_radius = _get_number(settings, "home_card_radius", 24)
    day_min_height = _get_number(settings, "home_day_min_height", 122)

    customer_bg = _rgba(customer, 0.13, "rgba(59, 130, 246, 0.13)")
    customer_border = _rgba(customer, 0.30, "rgba(96, 165, 250, 0.30)")
    general_bg = _rgba(general, 0.13, "rgba(34, 197, 94, 0.13)")
    general_border = _rgba(general, 0.30, "rgba(74, 222, 128, 0.30)")

    st.markdown(
        f"""
        <style>

        #MainMenu {{
            visibility: hidden;
        }}

        footer {{
            visibility: hidden;
        }}

        [data-testid="stSidebarNav"] {{
            display: none;
        }}

        header[data-testid="stHeader"] {{
            background: transparent;
        }}

        header[data-testid="stHeader"]::before {{
            background: transparent;
        }}

        .stApp {{
            background: {palette["app_bg"]};
            color: {palette["text_main"]};
        }}

        .block-container {{
            padding-top: 1.4rem;
            padding-bottom: 2.6rem;
            max-width: 1460px;
        }}

        h1, h2, h3, h4, h5, h6 {{
            color: {palette["text_main"]};
            letter-spacing: -0.04em;
        }}

        p, span, label {{
            color: {palette["text_sub"]};
        }}

        a {{
            color: {primary};
        }}

        hr {{
            border-color: {palette["card_border"]};
        }}

        [data-testid="stSidebar"] {{
            background: {palette["sidebar_bg"]};
            border-right: 1px solid {palette["card_border"]};
        }}

        [data-testid="stSidebar"] * {{
            color: {palette["text_main"]} !important;
        }}

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
            color: {palette["text_sub"]} !important;
        }}

        [data-testid="stSidebar"] .stButton > button {{
            min-height: 40px;
        }}

        .sidebar-profile-card {{
            background:
                linear-gradient(
                    135deg,
                    {_rgba(primary, 0.18, "rgba(91, 140, 255, 0.18)")},
                    {_rgba(secondary, 0.10, "rgba(124, 92, 255, 0.10)")}
                ),
                {palette["soft_bg"]};
            border: 1px solid rgba(148, 163, 184, 0.20);
            border-radius: 20px;
            padding: 18px;
            box-shadow: {palette["card_shadow"]};
        }}

        .sidebar-profile-title {{
            font-size: 13px;
            font-weight: 800;
            color: {palette["text_muted"]};
            margin-bottom: 8px;
        }}

        .sidebar-profile-name {{
            font-size: 19px;
            font-weight: 900;
            color: {palette["text_main"]};
            letter-spacing: -0.04em;
            margin-bottom: 5px;
        }}

        .sidebar-profile-role {{
            display: inline-block;
            border-radius: 999px;
            padding: 4px 9px;
            font-size: 11px;
            font-weight: 800;
            background: {_rgba(primary, 0.16, "rgba(91, 140, 255, 0.16)")};
            color: {secondary};
        }}

        .sidebar-section-title {{
            font-size: 13px;
            font-weight: 850;
            color: {palette["text_muted"]};
            margin-bottom: 10px;
        }}

        .crm-title {{
            font-size: 42px;
            line-height: 1.15;
            font-weight: 850;
            color: {palette["text_main"]};
            letter-spacing: -1.4px;
            margin-bottom: 8px;
        }}

        .crm-subtitle {{
            font-size: 16px;
            color: {palette["text_muted"]};
            margin-bottom: 22px;
        }}

        .crm-section-title {{
            font-size: 20px;
            font-weight: 800;
            color: {palette["text_main"]};
            margin-bottom: 14px;
            letter-spacing: -0.04em;
        }}

        .crm-muted {{
            color: {palette["text_muted"]};
            font-size: 14px;
        }}

        .crm-card {{
            background: {palette["card_bg"]};
            border: 1px solid {palette["card_border"]};
            border-radius: {card_radius}px;
            padding: 24px;
            backdrop-filter: blur(18px);
            box-shadow: {palette["card_shadow"]};
            margin-bottom: 18px;
        }}

        .crm-card-compact {{
            background: {palette["card_bg_soft"]};
            border: 1px solid {palette["card_border"]};
            border-radius: 20px;
            padding: 18px;
            backdrop-filter: blur(18px);
            box-shadow: {palette["card_shadow"]};
            margin-bottom: 14px;
        }}

        .crm-content-box {{
            padding: 14px 15px;
            border: 1px solid {palette["card_border"]};
            border-radius: 16px;
            background: {palette["soft_bg"]};
            color: {palette["text_sub"]};
            white-space: pre-wrap;
            line-height: 1.65;
            margin-bottom: 12px;
        }}

        .metric-card {{
            background:
                linear-gradient(
                    135deg,
                    {_rgba(primary, 0.18, "rgba(91, 140, 255, 0.18)")},
                    {_rgba(secondary, 0.08, "rgba(124, 92, 255, 0.08)")}
                ),
                {palette["card_bg"]};
            border: 1px solid {palette["card_border"]};
            border-radius: 22px;
            padding: 20px 22px;
            backdrop-filter: blur(18px);
            box-shadow: {palette["card_shadow"]};
            min-height: 112px;
        }}

        .metric-label {{
            color: {palette["text_sub"]};
            font-size: 14px;
            font-weight: 650;
            margin-bottom: 9px;
        }}

        .metric-value {{
            color: {palette["text_main"]};
            font-size: 31px;
            line-height: 1;
            font-weight: 850;
            letter-spacing: -0.05em;
            margin-bottom: 8px;
        }}

        .metric-desc {{
            color: {palette["text_muted"]};
            font-size: 13px;
        }}

        .crm-list-card,
        .recent-customer-card {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 18px;
            background: {palette["soft_bg"]};
            border: 1px solid {palette["card_border"]};
            border-radius: 20px;
            padding: 17px 18px;
            margin-bottom: 12px;
            transition: 0.15s ease;
        }}

        .crm-list-card:hover,
        .recent-customer-card:hover {{
            background: {palette["soft_hover"]};
            border-color: rgba(148, 163, 184, 0.24);
            transform: translateY(-1px);
        }}

        .customer-card-selected {{
            border-color: {_rgba(primary, 0.62, "rgba(91, 140, 255, 0.62)")};
            box-shadow: 0 0 0 1px {_rgba(primary, 0.28, "rgba(91, 140, 255, 0.28)")};
        }}

        .recent-customer-left {{
            display: flex;
            align-items: center;
            gap: 14px;
            min-width: 0;
        }}

        .recent-avatar {{
            width: 42px;
            height: 42px;
            border-radius: 15px;
            background: linear-gradient(135deg, {primary}, {secondary});
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 850;
            box-shadow: 0 10px 26px {_rgba(primary, 0.20, "rgba(91, 140, 255, 0.20)")};
            flex-shrink: 0;
        }}

        .recent-main {{
            min-width: 0;
        }}

        .recent-name {{
            color: {palette["text_main"]};
            font-size: 16px;
            font-weight: 800;
            margin-bottom: 4px;
            letter-spacing: -0.03em;
        }}

        .recent-meta {{
            color: {palette["text_muted"]};
            font-size: 13px;
            white-space: nowrap;
        }}

        .recent-customer-right {{
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 7px;
            flex-shrink: 0;
        }}

        .recent-sub {{
            color: {palette["text_sub"]};
            font-size: 12.5px;
            white-space: nowrap;
        }}

        .recent-status,
        .crm-badge {{
            border-radius: 999px;
            padding: 5px 10px;
            font-size: 12px;
            font-weight: 800;
            letter-spacing: -0.02em;
            border: 1px solid {palette["card_border"]};
            display: inline-block;
        }}

        .status-active {{
            color: #2563EB;
            background: rgba(59, 130, 246, 0.14);
            border-color: rgba(96, 165, 250, 0.28);
        }}

        .status-done {{
            color: #16A34A;
            background: rgba(34, 197, 94, 0.14);
            border-color: rgba(74, 222, 128, 0.26);
        }}

        .status-pending {{
            color: #B45309;
            background: rgba(245, 158, 11, 0.16);
            border-color: rgba(251, 191, 36, 0.26);
        }}

        .status-scheduled {{
            color: #7C3AED;
            background: rgba(139, 92, 246, 0.14);
            border-color: rgba(167, 139, 250, 0.28);
        }}

        .status-default {{
            color: {palette["text_sub"]};
            background: rgba(148, 163, 184, 0.13);
            border-color: rgba(148, 163, 184, 0.22);
        }}

        .home-month-title {{
            text-align: center;
            color: {palette["text_main"]};
            font-size: 28px;
            font-weight: 900;
            letter-spacing: -0.06em;
            padding-top: 6px;
        }}

        .home-upcoming-board {{
            background: {palette["card_bg"]};
            border: 1px solid {palette["card_border"]};
            border-radius: {card_radius}px;
            padding: 24px 28px;
            box-shadow: {palette["card_shadow"]};
            margin: 14px 0 24px 0;
        }}

        .home-upcoming-title {{
            color: {palette["text_main"]};
            text-align: center;
            font-size: 34px;
            font-weight: 850;
            letter-spacing: -0.06em;
            margin-bottom: 18px;
        }}

        .home-upcoming-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 12px;
        }}

        .home-upcoming-empty {{
            color: {palette["text_muted"]};
            text-align: center;
            grid-column: 1 / -1;
            padding: 16px;
            font-size: 16px;
        }}

        .home-upcoming-item {{
            display: flex;
            align-items: center;
            gap: 12px;
            background: {palette["soft_bg"]};
            border: 1px solid {palette["card_border"]};
            border-radius: 18px;
            padding: 13px;
            min-width: 0;
        }}

        .home-upcoming-date {{
            width: 48px;
            height: 48px;
            border-radius: 16px;
            background: linear-gradient(
                135deg,
                {_rgba(primary, 0.28, "rgba(91, 140, 255, 0.28)")},
                {_rgba(secondary, 0.18, "rgba(124, 92, 255, 0.18)")}
            );
            border: 1px solid {palette["card_border"]};
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }}

        .home-upcoming-day {{
            color: {palette["text_main"]};
            font-size: 18px;
            font-weight: 900;
            line-height: 1;
        }}

        .home-upcoming-month {{
            color: {palette["text_sub"]};
            font-size: 11px;
            margin-top: 3px;
        }}

        .home-upcoming-body {{
            min-width: 0;
        }}

        .home-upcoming-top {{
            display: flex;
            gap: 6px;
            align-items: center;
            margin-bottom: 4px;
            min-width: 0;
        }}

        .home-chip-type {{
            display: inline-block;
            border-radius: 999px;
            padding: 3px 7px;
            font-size: 10px;
            font-weight: 900;
            flex-shrink: 0;
        }}

        .home-chip-customer {{
            color: #BFDBFE;
            background: {customer_bg};
        }}

        .home-chip-general {{
            color: #BBF7D0;
            background: {general_bg};
        }}

        .home-upcoming-name {{
            color: {palette["text_main"]};
            font-size: 14px;
            font-weight: 850;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .home-upcoming-desc {{
            color: {palette["text_muted"]};
            font-size: 12px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .home-calendar-shell {{
            background: {palette["card_bg"]};
            border: 1px solid {palette["card_border"]};
            border-radius: {card_radius}px;
            padding: 18px;
            box-shadow: {palette["card_shadow"]};
        }}

        .home-weekday {{
            color: {palette["text_sub"]};
            font-size: 13px;
            font-weight: 850;
            text-align: center;
            padding: 8px 0 10px 0;
        }}

        .home-empty-day {{
            min-height: {day_min_height}px;
            border-radius: 18px;
            background: {palette["soft_bg"]};
            opacity: 0.25;
            margin-bottom: 10px;
        }}

        .home-calendar-event {{
            border-radius: 12px;
            padding: 5px 7px;
            margin-top: 5px;
            border: 1px solid {palette["card_border"]};
        }}

        .home-calendar-event.customer {{
            background: {customer_bg};
            border-color: {customer_border};
        }}

        .home-calendar-event.general {{
            background: {general_bg};
            border-color: {general_border};
        }}

        .home-calendar-event-title {{
            color: {palette["text_main"]};
            font-size: 11px;
            font-weight: 800;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .home-calendar-event-desc {{
            color: {palette["text_sub"]};
            font-size: 10px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .home-date-label {{
            display: inline-block;
            color: white;
            background: linear-gradient(135deg, #0F7490, #155E75);
            border: 2px solid rgba(15, 23, 42, 0.48);
            border-radius: 8px;
            padding: 4px 18px;
            font-size: 25px;
            font-weight: 850;
            letter-spacing: -0.05em;
            margin-left: 16px;
            margin-bottom: 10px;
        }}

        .home-selected-date {{
            color: {palette["text_main"]};
            font-size: 20px;
            font-weight: 850;
            letter-spacing: -0.04em;
            margin-left: 18px;
            margin-bottom: 14px;
        }}

        .home-right-dashed-box {{
            background: {palette["soft_bg"]};
            border: 3px dashed {palette["dash_border"]};
            border-radius: 34px;
            padding: 30px 28px;
            min-height: 330px;
            margin-bottom: 20px;
        }}

        .home-right-box-title {{
            color: {palette["text_main"]};
            text-align: center;
            font-size: 25px;
            font-weight: 850;
            letter-spacing: -0.05em;
            margin-bottom: 18px;
        }}

        .home-schedule-group {{
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-bottom: 14px;
        }}

        .home-schedule-item {{
            border-radius: 18px;
            padding: 14px 15px;
            border: 1px solid {palette["card_border"]};
        }}

        .home-schedule-customer {{
            background: {customer_bg};
            border-color: {customer_border};
        }}

        .home-schedule-general {{
            background: {general_bg};
            border-color: {general_border};
        }}

        .home-schedule-title {{
            color: {palette["text_main"]};
            font-size: 18px;
            font-weight: 850;
            letter-spacing: -0.04em;
            margin-bottom: 4px;
        }}

        .home-schedule-desc {{
            color: {palette["text_sub"]};
            font-size: 14px;
            line-height: 1.55;
        }}

        .home-schedule-meta {{
            color: {palette["text_muted"]};
            font-size: 12px;
            margin-top: 5px;
        }}

        .home-schedule-empty {{
            color: {palette["text_muted"]};
            text-align: center;
            padding: 12px;
            font-size: 14px;
        }}

        .home-right-form-title {{
            color: {palette["text_main"]};
            text-align: center;
            font-size: 24px;
            font-weight: 850;
            letter-spacing: -0.05em;
            margin-bottom: 14px;
        }}

        .today-action-card,
        .schedule-panel-card {{
            display: flex;
            justify-content: space-between;
            gap: 12px;
            background: {palette["soft_bg"]};
            border: 1px solid {palette["card_border"]};
            border-radius: 18px;
            padding: 15px;
            margin-bottom: 10px;
        }}

        .today-action-title {{
            color: {palette["text_main"]};
            font-size: 15px;
            font-weight: 850;
            margin-bottom: 4px;
        }}

        .today-action-meta {{
            color: {palette["text_muted"]};
            font-size: 12px;
        }}

        .today-action-right {{
            text-align: right;
            flex-shrink: 0;
        }}

        .today-action-badge {{
            color: #7C3AED;
            background: rgba(139, 92, 246, 0.14);
            border: 1px solid rgba(167, 139, 250, 0.28);
            border-radius: 999px;
            padding: 5px 9px;
            font-size: 11px;
            font-weight: 850;
            margin-bottom: 6px;
        }}

        .today-action-owner {{
            color: {palette["text_muted"]};
            font-size: 11px;
        }}

        .stButton > button {{
            border: none;
            border-radius: 15px;
            background: linear-gradient(135deg, {primary}, {secondary});
            color: white !important;
            font-weight: 750;
            min-height: 43px;
            box-shadow: 0 10px 28px {_rgba(primary, 0.18, "rgba(91, 140, 255, 0.18)")};
            transition: 0.15s ease;
        }}

        .stButton > button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 14px 34px {_rgba(primary, 0.26, "rgba(91, 140, 255, 0.26)")};
            border: none;
            color: white !important;
        }}

        .stButton > button:active {{
            transform: translateY(0px);
        }}

        .stFormSubmitButton > button {{
            border: none;
            border-radius: 15px;
            background: linear-gradient(135deg, {primary}, {secondary});
            color: white !important;
            font-weight: 800;
            min-height: 45px;
            box-shadow: 0 10px 28px {_rgba(primary, 0.18, "rgba(91, 140, 255, 0.18)")};
        }}

        .stTextInput > div > div > input,
        .stTextArea textarea,
        .stSelectbox div[data-baseweb="select"] > div,
        .stDateInput div[data-baseweb="input"] input {{
            background: {palette["input_bg"]};
            border: 1px solid {palette["input_border"]};
            border-radius: 14px;
            color: {palette["text_main"]};
        }}

        .stTextInput > label,
        .stTextArea > label,
        .stSelectbox > label,
        .stDateInput > label,
        .stRadio > label,
        .stCheckbox > label {{
            color: {palette["text_sub"]} !important;
            font-weight: 650;
        }}

        [data-testid="stForm"] {{
            background: {palette["card_bg_soft"]};
            border: 1px solid {palette["card_border"]};
            border-radius: 22px;
            padding: 22px;
            box-shadow: {palette["card_shadow"]};
        }}

        [data-testid="stDataFrame"] {{
            border-radius: 18px;
            overflow: hidden;
            border: 1px solid {palette["card_border"]};
            background: {palette["table_bg"]};
        }}

        [data-testid="stAlert"] {{
            border-radius: 18px;
            border: 1px solid {palette["card_border"]};
        }}

        [data-testid="stExpander"] {{
            border: 1px solid {palette["card_border"]};
            border-radius: 18px;
            background: {palette["card_bg_soft"]};
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-color: {palette["card_border"]} !important;
            border-radius: 20px !important;
            background: {palette["soft_bg"]} !important;
        }}

        @media screen and (max-width: 1000px) {{
            .home-upcoming-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
        }}

        @media screen and (max-width: 900px) {{
            .crm-title {{
                font-size: 32px;
            }}

            .metric-card {{
                min-height: 106px;
            }}

            .home-month-title {{
                font-size: 22px;
            }}

            .home-upcoming-grid {{
                grid-template-columns: 1fr;
            }}

            .crm-list-card,
            .recent-customer-card,
            .today-action-card,
            .schedule-panel-card {{
                flex-direction: column;
                align-items: flex-start;
            }}

            .recent-customer-right,
            .today-action-right {{
                align-items: flex-start;
                text-align: left;
            }}
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title, subtitle=None):
    safe_title = html.escape(str(title))

    st.markdown(
        f'<div class="crm-title">{safe_title}</div>',
        unsafe_allow_html=True,
    )

    if subtitle:
        safe_subtitle = html.escape(str(subtitle))

        st.markdown(
            f'<div class="crm-subtitle">{safe_subtitle}</div>',
            unsafe_allow_html=True,
        )


def render_metric_card(label, value, desc=""):
    safe_label = html.escape(str(label))
    safe_value = html.escape(str(value))
    safe_desc = html.escape(str(desc))

    st.markdown(
        (
            '<div class="metric-card">'
            f'<div class="metric-label">{safe_label}</div>'
            f'<div class="metric-value">{safe_value}</div>'
            f'<div class="metric-desc">{safe_desc}</div>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )


def render_section_title(title):
    safe_title = html.escape(str(title))

    st.markdown(
        f'<div class="crm-section-title">{safe_title}</div>',
        unsafe_allow_html=True,
    )


def render_card_start(extra_class=""):
    class_name = "crm-card"

    if extra_class:
        class_name = f"{class_name} {html.escape(str(extra_class))}"

    st.markdown(
        f'<div class="{class_name}">',
        unsafe_allow_html=True,
    )


def render_card_end():
    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


def render_badge(text, status_class="status-default"):
    safe_text = html.escape(str(text))

    st.markdown(
        f'<span class="crm-badge {status_class}">{safe_text}</span>',
        unsafe_allow_html=True,
    )


def get_status_class(status):
    status = str(status or "").strip()

    if "완료" in status or "계약" in status:
        return "status-done"

    if "진행" in status or "상담중" in status or "분석" in status:
        return "status-active"

    if "보류" in status or "실패" in status:
        return "status-pending"

    if "예정" in status or "제안" in status or "청약" in status:
        return "status-scheduled"

    return "status-default"