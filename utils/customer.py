from utils.db import get_conn


LEGACY_CUSTOMER_TYPE_MAP = {
    "신규고객": "DB고객",
    "기존고객": "기고객",
    "소개고객": "소개고객",
    "가망고객": "DB고객",
    "계약고객": "기고객",
}

LEGACY_STATUS_MAP = {
    "상담예정": "상담 예정",
    "상담중": "상담 중",
    "분석중": "설계 중",
    "제안완료": "설계 중",
    "청약예정": "설계 중",
    "계약완료": "계약 완료",
    "보류": "기타",
    "실패": "거절",
}


def _migrate_customer_options(cur):
    for old_value, new_value in LEGACY_CUSTOMER_TYPE_MAP.items():
        cur.execute(
            """
            UPDATE customers
            SET customer_type = ?
            WHERE customer_type = ?
            """,
            (new_value, old_value),
        )

    for old_value, new_value in LEGACY_STATUS_MAP.items():
        cur.execute(
            """
            UPDATE customers
            SET status = ?
            WHERE status = ?
            """,
            (new_value, old_value),
        )

    cur.execute(
        """
        UPDATE customers
        SET customer_type = '기타'
        WHERE customer_type IS NULL
           OR TRIM(customer_type) = ''
        """
    )

    cur.execute(
        """
        UPDATE customers
        SET status = '콜 대기'
        WHERE status IS NULL
           OR TRIM(status) = ''
        """
    )


def ensure_customer_columns():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(customers)")
    existing_columns = [row["name"] for row in cur.fetchall()]

    columns_to_add = {
        "customer_type": "TEXT",
        "carrier": "TEXT",
        "rrn": "TEXT",
        "address": "TEXT",
        "memo": "TEXT",
    }

    for column_name, column_type in columns_to_add.items():
        if column_name not in existing_columns:
            cur.execute(
                f"ALTER TABLE customers ADD COLUMN {column_name} {column_type}"
            )

    _migrate_customer_options(cur)

    conn.commit()
    conn.close()


def add_customer(
    owner_user_id,
    customer_type,
    name,
    phone="",
    carrier="",
    rrn="",
    address="",
    status="콜 대기",
    memo="",
):
    ensure_customer_columns()

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO customers
        (
            owner_user_id,
            customer_type,
            name,
            phone,
            carrier,
            rrn,
            address,
            status,
            memo
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            owner_user_id,
            customer_type,
            name,
            phone,
            carrier,
            rrn,
            address,
            status,
            memo,
        ),
    )

    conn.commit()
    conn.close()


def update_customer(
    customer_id,
    customer_type,
    name,
    phone,
    carrier,
    rrn,
    address,
    status,
    memo,
):
    ensure_customer_columns()

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE customers
        SET
            customer_type = ?,
            name = ?,
            phone = ?,
            carrier = ?,
            rrn = ?,
            address = ?,
            status = ?,
            memo = ?
        WHERE id = ?
        """,
        (
            customer_type,
            name,
            phone,
            carrier,
            rrn,
            address,
            status,
            memo,
            customer_id,
        ),
    )

    conn.commit()
    conn.close()


def delete_customer(customer_id, user):
    conn = get_conn()
    cur = conn.cursor()

    if user["role"] == "admin":
        cur.execute(
            "SELECT id FROM customers WHERE id = ?",
            (customer_id,),
        )
    else:
        cur.execute(
            """
            SELECT id
            FROM customers
            WHERE id = ?
              AND owner_user_id = ?
            """,
            (customer_id, user["id"]),
        )

    customer = cur.fetchone()

    if not customer:
        conn.close()
        return False

    cur.execute(
        "DELETE FROM consult_logs WHERE customer_id = ?",
        (customer_id,),
    )

    cur.execute(
        "DELETE FROM customers WHERE id = ?",
        (customer_id,),
    )

    conn.commit()
    conn.close()

    return True


def get_customers(user):
    ensure_customer_columns()

    conn = get_conn()
    cur = conn.cursor()

    if user["role"] == "admin":
        cur.execute(
            """
            SELECT
                c.id,
                c.customer_type,
                c.name,
                c.phone,
                c.carrier,
                c.rrn,
                c.address,
                c.status,
                c.memo,
                u.name AS owner_name,
                c.created_at
            FROM customers c
            JOIN users u
                ON c.owner_user_id = u.id
            ORDER BY c.created_at DESC
            """
        )
    else:
        cur.execute(
            """
            SELECT
                id,
                customer_type,
                name,
                phone,
                carrier,
                rrn,
                address,
                status,
                memo,
                created_at
            FROM customers
            WHERE owner_user_id = ?
            ORDER BY created_at DESC
            """,
            (user["id"],),
        )

    rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_customer_by_id(customer_id):
    ensure_customer_columns()

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            c.id,
            c.customer_type,
            c.name,
            c.phone,
            c.carrier,
            c.rrn,
            c.address,
            c.status,
            c.memo,
            c.owner_user_id,
            u.name AS owner_name,
            c.created_at
        FROM customers c
        JOIN users u
            ON c.owner_user_id = u.id
        WHERE c.id = ?
        """,
        (customer_id,),
    )

    row = cur.fetchone()
    conn.close()

    if row:
        return dict(row)

    return None