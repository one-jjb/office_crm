# C:\office_crm\tools\coverage_target_store.py

from pathlib import Path
from datetime import datetime
import sqlite3
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "db" / "crm.db"


DEFAULT_TARGET_COVERAGES = [
    "일반암 진단비",
    "유사암 진단비",
    "뇌혈관 진단비",
    "허혈성심장질환 진단비",
    "뇌혈관 수술비",
    "허혈성심장질환 수술비",
    "항암방사선치료비",
    "항암약물치료비",
    "표적항암치료비",
    "면역항암치료비",
    "양성자치료비",
    "중입자치료비",
    "세기조절방사선치료비",
    "상해사망",
    "질병수술비",
    "상해수술비",
    "질병입원일당",
    "상해입원일당",
    "간병인 입원일당",
    "운전자 담보",
    "실손의료비",
    "후유장해",
    "골절/화상",
]


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def clean_text(value):
    return str(value or "").strip()


def init_target_store():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS coverage_target_coverages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_label TEXT NOT NULL UNIQUE,
                sort_order INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                memo TEXT DEFAULT '',
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
        conn.commit()

    seed_default_targets_if_empty()


def seed_default_targets_if_empty():
    with get_conn() as conn:
        cur = conn.execute(
            """
            SELECT COUNT(*) AS cnt
            FROM coverage_target_coverages
            """
        )
        count = cur.fetchone()["cnt"]

        if count > 0:
            return

        now = now_str()

        for idx, label in enumerate(DEFAULT_TARGET_COVERAGES, start=1):
            conn.execute(
                """
                INSERT OR IGNORE INTO coverage_target_coverages (
                    target_label,
                    sort_order,
                    is_active,
                    memo,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, 1, '', ?, ?)
                """,
                (
                    label,
                    idx,
                    now,
                    now,
                ),
            )

        conn.commit()


def get_default_target_coverages():
    init_target_store()

    with get_conn() as conn:
        cur = conn.execute(
            """
            SELECT target_label
            FROM coverage_target_coverages
            WHERE is_active = 1
            ORDER BY sort_order ASC, id ASC
            """
        )

        labels = [row["target_label"] for row in cur.fetchall()]

    if labels:
        return labels

    return DEFAULT_TARGET_COVERAGES.copy()


def list_target_coverages(include_inactive=False):
    init_target_store()

    query = """
        SELECT
            id,
            target_label,
            sort_order,
            is_active,
            memo,
            created_at,
            updated_at
        FROM coverage_target_coverages
    """

    if not include_inactive:
        query += " WHERE is_active = 1"

    query += " ORDER BY sort_order ASC, id ASC"

    with get_conn() as conn:
        cur = conn.execute(query)
        return [dict(row) for row in cur.fetchall()]


def replace_target_coverages(labels):
    init_target_store()

    clean_labels = []
    seen = set()

    for label in labels:
        label = clean_text(label)

        if not label:
            continue

        if label in seen:
            continue

        seen.add(label)
        clean_labels.append(label)

    now = now_str()

    with get_conn() as conn:
        conn.execute(
            """
            UPDATE coverage_target_coverages
            SET is_active = 0,
                updated_at = ?
            """,
            (now,),
        )

        for idx, label in enumerate(clean_labels, start=1):
            conn.execute(
                """
                INSERT INTO coverage_target_coverages (
                    target_label,
                    sort_order,
                    is_active,
                    memo,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, 1, '', ?, ?)
                ON CONFLICT(target_label)
                DO UPDATE SET
                    sort_order = excluded.sort_order,
                    is_active = 1,
                    updated_at = excluded.updated_at
                """,
                (
                    label,
                    idx,
                    now,
                    now,
                ),
            )

        conn.commit()

    return {
        "success": True,
        "count": len(clean_labels),
        "message": f"{len(clean_labels)}개 목표 담보를 저장했습니다.",
    }


def upsert_target_coverage_by_id(row):
    init_target_store()

    try:
        row_id = int(row.get("id"))
    except Exception:
        return False

    label = clean_text(row.get("target_label"))
    memo = clean_text(row.get("memo"))

    try:
        sort_order = int(row.get("sort_order", 0))
    except Exception:
        sort_order = 0

    is_active = 1 if bool(row.get("is_active")) else 0

    if not label:
        return False

    now = now_str()

    with get_conn() as conn:
        cur = conn.execute(
            """
            UPDATE coverage_target_coverages
            SET
                target_label = ?,
                sort_order = ?,
                is_active = ?,
                memo = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                label,
                sort_order,
                is_active,
                memo,
                now,
                row_id,
            ),
        )
        conn.commit()

    return cur.rowcount > 0


def add_target_coverage(target_label, sort_order=0, memo=""):
    init_target_store()

    target_label = clean_text(target_label)
    memo = clean_text(memo)

    if not target_label:
        return False

    try:
        sort_order = int(sort_order)
    except Exception:
        sort_order = 0

    now = now_str()

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO coverage_target_coverages (
                target_label,
                sort_order,
                is_active,
                memo,
                created_at,
                updated_at
            )
            VALUES (?, ?, 1, ?, ?, ?)
            ON CONFLICT(target_label)
            DO UPDATE SET
                sort_order = excluded.sort_order,
                is_active = 1,
                memo = excluded.memo,
                updated_at = excluded.updated_at
            """,
            (
                target_label,
                sort_order,
                memo,
                now,
                now,
            ),
        )
        conn.commit()

    return True


def delete_target_coverage(row_id):
    init_target_store()

    try:
        row_id = int(row_id)
    except Exception:
        return False

    now = now_str()

    with get_conn() as conn:
        cur = conn.execute(
            """
            UPDATE coverage_target_coverages
            SET is_active = 0,
                updated_at = ?
            WHERE id = ?
            """,
            (
                now,
                row_id,
            ),
        )
        conn.commit()

    return cur.rowcount > 0


def export_target_coverages_to_dataframe():
    rows = list_target_coverages(include_inactive=True)
    return pd.DataFrame(rows)


def import_target_coverages_from_dataframe(df):
    if df is None or df.empty:
        return {
            "success": False,
            "count": 0,
            "message": "가져올 데이터가 없습니다.",
        }

    labels = []

    for _, row in df.iterrows():
        label = clean_text(
            row.get(
                "target_label",
                row.get(
                    "목표담보명",
                    row.get(
                        "목표 담보명",
                        "",
                    ),
                ),
            )
        )

        if label:
            labels.append(label)

    return replace_target_coverages(labels)