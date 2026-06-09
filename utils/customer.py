from utils.db import get_conn


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
        "memo": "TEXT"
    }

    for column_name, column_type in columns_to_add.items():
        if column_name not in existing_columns:
            cur.execute(
                f"ALTER TABLE customers ADD COLUMN {column_name} {column_type}"
            )

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
    status="상담중",
    memo=""
):
    ensure_customer_columns()

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
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
    """, (
        owner_user_id,
        customer_type,
        name,
        phone,
        carrier,
        rrn,
        address,
        status,
        memo
    ))

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
    memo
):
    ensure_customer_columns()

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
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
    """, (
        customer_type,
        name,
        phone,
        carrier,
        rrn,
        address,
        status,
        memo,
        customer_id
    ))

    conn.commit()
    conn.close()


def delete_customer(customer_id, user):
    conn = get_conn()
    cur = conn.cursor()

    if user["role"] == "admin":
        cur.execute(
            "SELECT id FROM customers WHERE id = ?",
            (customer_id,)
        )
    else:
        cur.execute(
            """
            SELECT id
            FROM customers
            WHERE id = ?
              AND owner_user_id = ?
            """,
            (customer_id, user["id"])
        )

    customer = cur.fetchone()

    if not customer:
        conn.close()
        return False

    cur.execute(
        "DELETE FROM consult_logs WHERE customer_id = ?",
        (customer_id,)
    )

    cur.execute(
        "DELETE FROM customers WHERE id = ?",
        (customer_id,)
    )

    conn.commit()
    conn.close()

    return True


def get_customers(user):
    ensure_customer_columns()

    conn = get_conn()
    cur = conn.cursor()

    if user["role"] == "admin":
        cur.execute("""
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
        """)
    else:
        cur.execute("""
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
        """, (user["id"],))

    rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_customer_by_id(customer_id):
    ensure_customer_columns()

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
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
    """, (customer_id,))

    row = cur.fetchone()
    conn.close()

    if row:
        return dict(row)

    return None