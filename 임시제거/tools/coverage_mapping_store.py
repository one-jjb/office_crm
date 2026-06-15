from pathlib import Path
from datetime import datetime
import sqlite3
import re


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "db" / "crm.db"


VALID_STATUSES = ["자동매핑", "확인필요", "매핑 제외"]
VALID_SCOPES = ["product", "company", "global"]


def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def clean_text(value):
    text = str(value or "")
    text = text.replace("_x000D_", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_text(value):
    text = clean_text(value)

    for ch in [
        " ", "\n", "\t", "\r",
        "-", "_",
        "(", ")", "[", "]",
        "/", "\\",
        ",", ".", "·", "ㆍ",
        ":",
    ]:
        text = text.replace(ch, "")

    return text.lower().strip()


def normalize_status(value):
    status = clean_text(value)
    if status in VALID_STATUSES:
        return status
    return "확인필요"


def normalize_scope(value):
    scope = clean_text(value) or "product"
    if scope not in VALID_SCOPES:
        return "product"
    return scope


def normalize_target_for_save(target_label, status):
    """
    저장소에는 확인필요 행도 반드시 남겨야 한다.
    - 자동매핑: target_label이 있어야 의미가 있음
    - 확인필요: target_label이 비어 있거나 '매핑 제외'여도 저장해야 함
    - 매핑 제외: 저장하지 않음
    """
    target_label = clean_text(target_label)
    status = normalize_status(status)

    if status == "확인필요" and target_label == "매핑 제외":
        return ""

    return target_label


def split_mapping_labels(value):
    text = str(value or "").strip()

    if not text:
        return []

    parts = re.split(r"[|,\n;]+", text)

    labels = []
    seen = set()

    for part in parts:
        label = clean_text(part)

        if not label:
            continue

        if label in seen:
            continue

        seen.add(label)
        labels.append(label)

    return labels


def init_mapping_store():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS coverage_mapping_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scope TEXT DEFAULT 'product',
                company TEXT DEFAULT '',
                product TEXT DEFAULT '',
                contract_date TEXT DEFAULT '',
                company_coverage_name TEXT DEFAULT '',
                credit_coverage_name TEXT DEFAULT '',
                source_name TEXT DEFAULT '',
                amount TEXT DEFAULT '',
                target_label TEXT DEFAULT '',
                status TEXT DEFAULT '자동매핑',
                use_count INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT,
                last_used_at TEXT,
                memo TEXT DEFAULT ''
            )
            """
        )
        conn.commit()


def ensure_column(column_name, column_type):
    init_mapping_store()

    with get_conn() as conn:
        cur = conn.execute("PRAGMA table_info(coverage_mapping_rules)")
        columns = [row["name"] for row in cur.fetchall()]

        if column_name not in columns:
            conn.execute(
                f"""
                ALTER TABLE coverage_mapping_rules
                ADD COLUMN {column_name} {column_type}
                """
            )
            conn.commit()


def migrate_columns():
    init_mapping_store()

    required_columns = {
        "scope": "TEXT DEFAULT 'product'",
        "company": "TEXT DEFAULT ''",
        "product": "TEXT DEFAULT ''",
        "contract_date": "TEXT DEFAULT ''",
        "company_coverage_name": "TEXT DEFAULT ''",
        "credit_coverage_name": "TEXT DEFAULT ''",
        "source_name": "TEXT DEFAULT ''",
        "amount": "TEXT DEFAULT ''",
        "target_label": "TEXT DEFAULT ''",
        "status": "TEXT DEFAULT '자동매핑'",
        "use_count": "INTEGER DEFAULT 0",
        "created_at": "TEXT",
        "updated_at": "TEXT",
        "last_used_at": "TEXT",
        "memo": "TEXT DEFAULT ''",
    }

    for column_name, column_type in required_columns.items():
        ensure_column(column_name, column_type)


migrate_columns()


def list_mapping_rules(limit=5000):
    init_mapping_store()

    with get_conn() as conn:
        cur = conn.execute(
            """
            SELECT *
            FROM coverage_mapping_rules
            ORDER BY updated_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        )

        return [dict(row) for row in cur.fetchall()]


def delete_mapping_rule(rule_id):
    init_mapping_store()

    try:
        rule_id = int(rule_id)
    except Exception:
        return False

    with get_conn() as conn:
        cur = conn.execute(
            """
            DELETE FROM coverage_mapping_rules
            WHERE id = ?
            """,
            (rule_id,),
        )
        conn.commit()

    return cur.rowcount > 0


def delete_mapping_rules(rule_ids):
    init_mapping_store()

    clean_ids = []

    for rule_id in rule_ids:
        try:
            clean_ids.append(int(rule_id))
        except Exception:
            continue

    if not clean_ids:
        return 0

    placeholders = ",".join(["?"] * len(clean_ids))

    with get_conn() as conn:
        cur = conn.execute(
            f"""
            DELETE FROM coverage_mapping_rules
            WHERE id IN ({placeholders})
            """,
            clean_ids,
        )
        conn.commit()

    return cur.rowcount


def increase_use_count(rule_id):
    try:
        rule_id = int(rule_id)
    except Exception:
        return False

    with get_conn() as conn:
        conn.execute(
            """
            UPDATE coverage_mapping_rules
            SET
                use_count = COALESCE(use_count, 0) + 1,
                last_used_at = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                now_str(),
                now_str(),
                rule_id,
            ),
        )
        conn.commit()

    return True


def find_existing_rule(
    scope="product",
    company="",
    product="",
    contract_date="",
    source_name="",
    company_coverage_name="",
    credit_coverage_name="",
    target_label="",
):
    init_mapping_store()

    scope = normalize_scope(scope)
    company = clean_text(company)
    product = clean_text(product)
    contract_date = clean_text(contract_date)
    source_name = clean_text(source_name)
    company_coverage_name = clean_text(company_coverage_name)
    credit_coverage_name = clean_text(credit_coverage_name)
    target_label = clean_text(target_label)

    with get_conn() as conn:
        cur = conn.execute(
            """
            SELECT *
            FROM coverage_mapping_rules
            ORDER BY updated_at DESC, id DESC
            """
        )
        rows = [dict(row) for row in cur.fetchall()]

    target_norm = normalize_text(target_label)

    for row in rows:
        row_scope = clean_text(row.get("scope", "product"))

        if row_scope != scope:
            continue

        if row_scope in ["company", "product"]:
            if normalize_text(row.get("company")) != normalize_text(company):
                continue

        if row_scope == "product":
            if normalize_text(row.get("product")) != normalize_text(product):
                continue

        # 자동매핑/복수매핑은 target_label까지 같은 룰을 업데이트한다.
        # 확인필요처럼 target_label이 비어 있는 행은 담보명 기준으로만 기존 행을 찾는다.
        if target_norm:
            if normalize_text(row.get("target_label")) != target_norm:
                continue

        compare_candidates = [
            (
                normalize_text(row.get("source_name")),
                normalize_text(source_name),
            ),
            (
                normalize_text(row.get("company_coverage_name")),
                normalize_text(company_coverage_name),
            ),
            (
                normalize_text(row.get("credit_coverage_name")),
                normalize_text(credit_coverage_name),
            ),
        ]

        for saved_value, input_value in compare_candidates:
            if saved_value and input_value and saved_value == input_value:
                return row

    return None


def save_mapping_rule(
    source_name="",
    company_coverage_name="",
    credit_coverage_name="",
    target_label="",
    status="자동매핑",
    company="",
    product="",
    contract_date="",
    amount="",
    scope="product",
    memo="",
):
    init_mapping_store()

    source_name = clean_text(source_name)
    company_coverage_name = clean_text(company_coverage_name)
    credit_coverage_name = clean_text(credit_coverage_name)
    status = normalize_status(status)
    company = clean_text(company)
    product = clean_text(product)
    contract_date = clean_text(contract_date)
    amount = clean_text(amount)
    scope = normalize_scope(scope)
    memo = clean_text(memo)
    target_label = normalize_target_for_save(target_label, status)

    if not source_name:
        source_name = company_coverage_name or credit_coverage_name

    if not source_name and not company_coverage_name and not credit_coverage_name:
        return False

    # 사용자가 명시적으로 매핑 제외로 저장한 행은 저장소에 넣지 않는다.
    if status == "매핑 제외":
        return False

    labels = split_mapping_labels(target_label)

    # 핵심 수정:
    # 확인필요는 target_label이 비어 있어도 저장한다.
    if not labels:
        if status != "확인필요":
            return False
        labels = [""]

    saved_any = False
    now = now_str()

    with get_conn() as conn:
        for label in labels:
            existing = find_existing_rule(
                scope=scope,
                company=company,
                product=product,
                contract_date=contract_date,
                source_name=source_name,
                company_coverage_name=company_coverage_name,
                credit_coverage_name=credit_coverage_name,
                target_label=label,
            )

            if existing:
                conn.execute(
                    """
                    UPDATE coverage_mapping_rules
                    SET
                        scope = ?,
                        company = ?,
                        product = ?,
                        contract_date = ?,
                        source_name = ?,
                        company_coverage_name = ?,
                        credit_coverage_name = ?,
                        amount = ?,
                        target_label = ?,
                        status = ?,
                        updated_at = ?,
                        memo = ?
                    WHERE id = ?
                    """,
                    (
                        scope,
                        company,
                        product,
                        contract_date,
                        source_name,
                        company_coverage_name,
                        credit_coverage_name,
                        amount,
                        label,
                        status,
                        now,
                        memo,
                        existing["id"],
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO coverage_mapping_rules (
                        scope,
                        company,
                        product,
                        contract_date,
                        source_name,
                        company_coverage_name,
                        credit_coverage_name,
                        amount,
                        target_label,
                        status,
                        use_count,
                        created_at,
                        updated_at,
                        last_used_at,
                        memo
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        scope,
                        company,
                        product,
                        contract_date,
                        source_name,
                        company_coverage_name,
                        credit_coverage_name,
                        amount,
                        label,
                        status,
                        0,
                        now,
                        now,
                        None,
                        memo,
                    ),
                )

            saved_any = True

        conn.commit()

    return saved_any


def upsert_mapping_rule_by_id(row):
    init_mapping_store()

    try:
        rule_id = int(row.get("id"))
    except Exception:
        return False

    now = now_str()

    with get_conn() as conn:
        cur = conn.execute(
            """
            UPDATE coverage_mapping_rules
            SET
                scope = ?,
                company = ?,
                product = ?,
                contract_date = ?,
                source_name = ?,
                company_coverage_name = ?,
                credit_coverage_name = ?,
                amount = ?,
                target_label = ?,
                status = ?,
                updated_at = ?,
                memo = ?
            WHERE id = ?
            """,
            (
                normalize_scope(row.get("scope", "product")),
                clean_text(row.get("company", "")),
                clean_text(row.get("product", "")),
                clean_text(row.get("contract_date", "")),
                clean_text(row.get("source_name", "")),
                clean_text(row.get("company_coverage_name", "")),
                clean_text(row.get("credit_coverage_name", "")),
                clean_text(row.get("amount", "")),
                clean_text(row.get("target_label", "")),
                normalize_status(row.get("status", "확인필요")),
                now,
                clean_text(row.get("memo", "")),
                rule_id,
            ),
        )
        conn.commit()

    return cur.rowcount > 0


def search_mapping_rules(
    source_name="",
    company_coverage_name="",
    credit_coverage_name="",
    company="",
    product="",
):
    init_mapping_store()

    source_norm = normalize_text(source_name)
    company_cov_norm = normalize_text(company_coverage_name)
    credit_cov_norm = normalize_text(credit_coverage_name)
    company_norm = normalize_text(company)
    product_norm = normalize_text(product)

    with get_conn() as conn:
        cur = conn.execute(
            """
            SELECT *
            FROM coverage_mapping_rules
            ORDER BY use_count DESC, updated_at DESC, id DESC
            """
        )
        rows = [dict(row) for row in cur.fetchall()]

    matched = []

    for row in rows:
        # 확인필요/매핑 제외 룰은 자동매핑 재사용 대상에서 제외한다.
        if clean_text(row.get("status")) != "자동매핑":
            continue

        if not clean_text(row.get("target_label")):
            continue

        row_scope = clean_text(row.get("scope", "product"))

        if row_scope in ["company", "product"] and company_norm:
            if normalize_text(row.get("company")) != company_norm:
                continue

        if row_scope == "product" and product_norm:
            if normalize_text(row.get("product")) != product_norm:
                continue

        compare_items = [
            normalize_text(row.get("source_name")),
            normalize_text(row.get("company_coverage_name")),
            normalize_text(row.get("credit_coverage_name")),
        ]

        input_items = [
            source_norm,
            company_cov_norm,
            credit_cov_norm,
        ]

        matched_flag = False

        for compare_item in compare_items:
            if not compare_item:
                continue

            for input_item in input_items:
                if not input_item:
                    continue

                if compare_item == input_item:
                    matched_flag = True
                    break

            if matched_flag:
                break

        if matched_flag:
            matched.append(row)

    return matched


def find_saved_mapping(
    company="",
    product="",
    source_name="",
    company_coverage_name="",
    credit_coverage_name="",
):
    matches = search_mapping_rules(
        source_name=source_name,
        company_coverage_name=company_coverage_name,
        credit_coverage_name=credit_coverage_name,
        company=company,
        product=product,
    )

    if not matches:
        return None

    best = matches[0]

    rule_id = best.get("id")

    if rule_id:
        increase_use_count(rule_id)

    return best


def save_confirmed_mappings(mapping_df, default_scope="product"):
    if mapping_df is None or mapping_df.empty:
        return {
            "saved": 0,
            "skipped": 0,
        }

    saved = 0
    skipped = 0

    for _, row in mapping_df.iterrows():
        row_dict = row.to_dict()

        status = normalize_status(
            row_dict.get("상태", row_dict.get("status", "확인필요"))
        )

        target_label = clean_text(
            row_dict.get(
                "확정위치",
                row_dict.get(
                    "매핑대상",
                    row_dict.get(
                        "target_label",
                        "",
                    ),
                ),
            )
        )

        if not target_label:
            target_label = clean_text(row_dict.get("추천위치", ""))

        # 사용자가 직접 제외한 것만 저장하지 않는다.
        if status == "매핑 제외":
            skipped += 1
            continue

        # 확인필요인데 추천값이 '매핑 제외'인 경우도 저장소에는 확인필요/빈 매핑대상으로 남긴다.
        target_label = normalize_target_for_save(target_label, status)

        # 자동매핑인데 매핑대상이 없으면 자동매핑으로 볼 수 없으므로 확인필요로 강등 저장한다.
        if status == "자동매핑" and not target_label:
            status = "확인필요"

        ok = save_mapping_rule(
            source_name=row_dict.get(
                "추출담보명",
                row_dict.get("source_name", ""),
            ),
            company_coverage_name=row_dict.get(
                "회사담보명",
                row_dict.get("company_coverage_name", ""),
            ),
            credit_coverage_name=row_dict.get(
                "신정원담보명",
                row_dict.get("credit_coverage_name", ""),
            ),
            target_label=target_label,
            status=status,
            company=row_dict.get(
                "보험사",
                row_dict.get("company", ""),
            ),
            product=row_dict.get(
                "상품명",
                row_dict.get("product", ""),
            ),
            contract_date=row_dict.get(
                "가입시기",
                row_dict.get("contract_date", ""),
            ),
            amount=row_dict.get(
                "보장금액",
                row_dict.get("amount", ""),
            ),
            scope=row_dict.get(
                "저장범위",
                row_dict.get("scope", default_scope),
            ),
            memo=row_dict.get(
                "메모",
                row_dict.get("memo", ""),
            ),
        )

        if ok:
            label_count = len(split_mapping_labels(target_label))
            saved += max(1, label_count)
        else:
            skipped += 1

    return {
        "saved": saved,
        "skipped": skipped,
    }
