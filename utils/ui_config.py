from utils.db import get_conn


def _default_settings():
    return [
        # =====================================================
        # 색상 설정
        # =====================================================
        {
            "setting_key": "primary_color",
            "label": "메인 버튼 색상",
            "value": "#5B8CFF",
            "default_value": "#5B8CFF",
            "input_type": "color",
            "group_name": "색상 설정",
            "sort_order": 10,
            "description": "주요 버튼과 강조 색상에 사용됩니다.",
        },
        {
            "setting_key": "secondary_color",
            "label": "보조 버튼 색상",
            "value": "#7C5CFF",
            "default_value": "#7C5CFF",
            "input_type": "color",
            "group_name": "색상 설정",
            "sort_order": 20,
            "description": "메인 색상과 함께 그라데이션에 사용됩니다.",
        },
        {
            "setting_key": "customer_color",
            "label": "고객일정 색상",
            "value": "#3B82F6",
            "default_value": "#3B82F6",
            "input_type": "color",
            "group_name": "색상 설정",
            "sort_order": 30,
            "description": "고객일정 카드와 뱃지 색상에 사용됩니다.",
        },
        {
            "setting_key": "general_color",
            "label": "일반일정 색상",
            "value": "#22C55E",
            "default_value": "#22C55E",
            "input_type": "color",
            "group_name": "색상 설정",
            "sort_order": 40,
            "description": "일반일정 카드와 뱃지 색상에 사용됩니다.",
        },

        # =====================================================
        # 메인 화면 문구
        # =====================================================
        {
            "setting_key": "home_upcoming_title",
            "label": "다가오는 일정 제목",
            "value": "다가오는 일정",
            "default_value": "다가오는 일정",
            "input_type": "text",
            "group_name": "메인 화면 문구",
            "sort_order": 100,
            "description": "메인 화면 상단 일정 박스 제목입니다.",
        },
        {
            "setting_key": "home_date_label",
            "label": "오른쪽 날짜 라벨",
            "value": "날짜",
            "default_value": "날짜",
            "input_type": "text",
            "group_name": "메인 화면 문구",
            "sort_order": 110,
            "description": "오른쪽 일정 패널 상단 라벨입니다.",
        },
        {
            "setting_key": "home_schedule_box_title",
            "label": "오른쪽 일정 박스 제목",
            "value": "일정",
            "default_value": "일정",
            "input_type": "text",
            "group_name": "메인 화면 문구",
            "sort_order": 120,
            "description": "선택한 날짜의 일정 목록 제목입니다.",
        },
        {
            "setting_key": "home_general_form_add_title",
            "label": "일반일정 추가 폼 제목",
            "value": "일반일정 입력 / 저장",
            "default_value": "일반일정 입력 / 저장",
            "input_type": "text",
            "group_name": "메인 화면 문구",
            "sort_order": 130,
            "description": "새 일반일정을 입력할 때 표시되는 제목입니다.",
        },
        {
            "setting_key": "home_general_form_edit_title",
            "label": "일반일정 수정 폼 제목",
            "value": "일반일정 수정",
            "default_value": "일반일정 수정",
            "input_type": "text",
            "group_name": "메인 화면 문구",
            "sort_order": 140,
            "description": "기존 일반일정을 수정할 때 표시되는 제목입니다.",
        },

        # =====================================================
        # KPI 문구
        # =====================================================
        {
            "setting_key": "metric_total_label",
            "label": "KPI 전체 고객 제목",
            "value": "전체 고객",
            "default_value": "전체 고객",
            "input_type": "text",
            "group_name": "KPI 문구",
            "sort_order": 200,
            "description": "메인 KPI 카드 제목입니다.",
        },
        {
            "setting_key": "metric_total_desc",
            "label": "KPI 전체 고객 설명",
            "value": "등록된 고객 수",
            "default_value": "등록된 고객 수",
            "input_type": "text",
            "group_name": "KPI 문구",
            "sort_order": 210,
            "description": "메인 KPI 카드 설명입니다.",
        },
        {
            "setting_key": "metric_customer_schedule_label",
            "label": "KPI 고객일정 제목",
            "value": "고객일정",
            "default_value": "고객일정",
            "input_type": "text",
            "group_name": "KPI 문구",
            "sort_order": 220,
            "description": "고객일정 KPI 카드 제목입니다.",
        },
        {
            "setting_key": "metric_customer_schedule_desc",
            "label": "KPI 고객일정 설명",
            "value": "상담 이력 기준",
            "default_value": "상담 이력 기준",
            "input_type": "text",
            "group_name": "KPI 문구",
            "sort_order": 230,
            "description": "고객일정 KPI 카드 설명입니다.",
        },
        {
            "setting_key": "metric_general_schedule_label",
            "label": "KPI 일반일정 제목",
            "value": "일반일정",
            "default_value": "일반일정",
            "input_type": "text",
            "group_name": "KPI 문구",
            "sort_order": 240,
            "description": "일반일정 KPI 카드 제목입니다.",
        },
        {
            "setting_key": "metric_general_schedule_desc",
            "label": "KPI 일반일정 설명",
            "value": "직접 등록 일정",
            "default_value": "직접 등록 일정",
            "input_type": "text",
            "group_name": "KPI 문구",
            "sort_order": 250,
            "description": "일반일정 KPI 카드 설명입니다.",
        },
        {
            "setting_key": "metric_active_customer_label",
            "label": "KPI 진행 고객 제목",
            "value": "진행 고객",
            "default_value": "진행 고객",
            "input_type": "text",
            "group_name": "KPI 문구",
            "sort_order": 260,
            "description": "진행 고객 KPI 카드 제목입니다.",
        },
        {
            "setting_key": "metric_active_customer_desc",
            "label": "KPI 진행 고객 설명",
            "value": "진행 상태 고객",
            "default_value": "진행 상태 고객",
            "input_type": "text",
            "group_name": "KPI 문구",
            "sort_order": 270,
            "description": "진행 고객 KPI 카드 설명입니다.",
        },

        # =====================================================
        # 표시 설정
        # =====================================================
        {
            "setting_key": "show_home_upcoming",
            "label": "다가오는 일정 표시",
            "value": "true",
            "default_value": "true",
            "input_type": "toggle",
            "group_name": "표시 설정",
            "sort_order": 300,
            "description": "메인 화면 상단의 다가오는 일정 영역을 표시합니다.",
        },
        {
            "setting_key": "show_home_metrics",
            "label": "KPI 카드 표시",
            "value": "true",
            "default_value": "true",
            "input_type": "toggle",
            "group_name": "표시 설정",
            "sort_order": 310,
            "description": "전체 고객, 고객일정, 일반일정, 진행 고객 카드를 표시합니다.",
        },
        {
            "setting_key": "show_customer_edit_buttons",
            "label": "고객일정 수정 버튼 표시",
            "value": "true",
            "default_value": "true",
            "input_type": "toggle",
            "group_name": "표시 설정",
            "sort_order": 320,
            "description": "고객일정을 상담 이력에서 수정하는 버튼을 표시합니다.",
        },
        {
            "setting_key": "show_general_schedule_manager",
            "label": "일반일정 수정/삭제 버튼 표시",
            "value": "true",
            "default_value": "true",
            "input_type": "toggle",
            "group_name": "표시 설정",
            "sort_order": 330,
            "description": "일반일정 수정/삭제 버튼을 표시합니다.",
        },
        {
            "setting_key": "show_general_schedule_form",
            "label": "일반일정 입력 폼 표시",
            "value": "true",
            "default_value": "true",
            "input_type": "toggle",
            "group_name": "표시 설정",
            "sort_order": 340,
            "description": "오른쪽 패널 하단 일반일정 입력 폼을 표시합니다.",
        },

        # =====================================================
        # 화면 옵션
        # =====================================================
        {
            "setting_key": "home_upcoming_count",
            "label": "다가오는 일정 표시 개수",
            "value": "4",
            "default_value": "4",
            "input_type": "number",
            "group_name": "화면 옵션",
            "sort_order": 400,
            "description": "다가오는 일정 영역에 표시할 최대 개수입니다.",
        },
        {
            "setting_key": "calendar_event_limit",
            "label": "달력 칸 일정 표시 개수",
            "value": "2",
            "default_value": "2",
            "input_type": "number",
            "group_name": "화면 옵션",
            "sort_order": 410,
            "description": "달력 날짜 한 칸에 보여줄 고객/일반 일정 개수입니다.",
        },
        {
            "setting_key": "home_card_radius",
            "label": "카드 둥근 정도",
            "value": "24",
            "default_value": "24",
            "input_type": "number",
            "group_name": "화면 옵션",
            "sort_order": 420,
            "description": "메인 화면 카드의 둥근 정도입니다.",
        },
        {
            "setting_key": "home_day_min_height",
            "label": "달력 빈 칸 높이",
            "value": "122",
            "default_value": "122",
            "input_type": "number",
            "group_name": "화면 옵션",
            "sort_order": 430,
            "description": "달력 날짜 칸의 기본 높이 기준입니다.",
        },
    ]


def ensure_ui_settings_table():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS ui_settings (
            setting_key TEXT PRIMARY KEY,
            label TEXT NOT NULL,
            value TEXT,
            default_value TEXT,
            input_type TEXT NOT NULL,
            group_name TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0,
            description TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    for item in _default_settings():
        cur.execute("""
            INSERT INTO ui_settings
            (
                setting_key,
                label,
                value,
                default_value,
                input_type,
                group_name,
                sort_order,
                description
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET
                label = excluded.label,
                default_value = excluded.default_value,
                input_type = excluded.input_type,
                group_name = excluded.group_name,
                sort_order = excluded.sort_order,
                description = excluded.description
        """, (
            item["setting_key"],
            item["label"],
            item["value"],
            item["default_value"],
            item["input_type"],
            item["group_name"],
            item["sort_order"],
            item["description"],
        ))

    conn.commit()
    conn.close()


def get_ui_settings_rows():
    ensure_ui_settings_table()

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            setting_key,
            label,
            value,
            default_value,
            input_type,
            group_name,
            sort_order,
            description,
            updated_at
        FROM ui_settings
        ORDER BY
            group_name,
            sort_order,
            setting_key
    """)

    rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_ui_settings_map():
    rows = get_ui_settings_rows()
    result = {}

    for row in rows:
        value = row.get("value")

        if value is None or str(value).strip() == "":
            value = row.get("default_value")

        result[row["setting_key"]] = value

    return result


def get_ui_setting(setting_key, default=None):
    settings = get_ui_settings_map()
    value = settings.get(setting_key)

    if value is None or str(value).strip() == "":
        return default

    return value


def get_ui_text(setting_key, default=""):
    value = get_ui_setting(setting_key, default)

    if value is None:
        return default

    return str(value)


def get_ui_int(setting_key, default=0):
    value = get_ui_setting(setting_key, default)

    try:
        return int(float(value))
    except Exception:
        return default


def get_ui_bool(setting_key, default=False):
    value = get_ui_setting(
        setting_key,
        "true" if default else "false",
    )

    if isinstance(value, bool):
        return value

    return str(value).strip().lower() in [
        "true",
        "1",
        "yes",
        "y",
        "on",
    ]


def update_ui_setting(setting_key, value):
    ensure_ui_settings_table()

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE ui_settings
        SET
            value = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE setting_key = ?
    """, (
        str(value),
        setting_key,
    ))

    conn.commit()
    conn.close()


def update_many_ui_settings(settings):
    ensure_ui_settings_table()

    conn = get_conn()
    cur = conn.cursor()

    for setting_key, value in settings.items():
        cur.execute("""
            UPDATE ui_settings
            SET
                value = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE setting_key = ?
        """, (
            str(value),
            setting_key,
        ))

    conn.commit()
    conn.close()


def reset_ui_settings_to_defaults():
    ensure_ui_settings_table()

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE ui_settings
        SET
            value = default_value,
            updated_at = CURRENT_TIMESTAMP
    """)

    conn.commit()
    conn.close()