from utils.db import get_conn


def ensure_consult_columns():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS consult_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            consult_date TEXT NOT NULL,
            content TEXT NOT NULL,
            next_action TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(customer_id) REFERENCES customers(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    cur.execute("PRAGMA table_info(consult_logs)")
    existing_columns = [row["name"] for row in cur.fetchall()]

    if "next_action_date" not in existing_columns:
        cur.execute("ALTER TABLE consult_logs ADD COLUMN next_action_date TEXT")

    conn.commit()
    conn.close()


def add_consult_log(
    customer_id,
    user_id,
    consult_date,
    content,
    next_action="",
    next_action_date=""
):
    ensure_consult_columns()

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO consult_logs
        (
            customer_id,
            user_id,
            consult_date,
            content,
            next_action,
            next_action_date
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        customer_id,
        user_id,
        consult_date,
        content,
        next_action,
        next_action_date
    ))

    conn.commit()
    conn.close()


def get_consult_logs(customer_id):
    ensure_consult_columns()

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            cl.id,
            cl.consult_date,
            cl.content,
            cl.next_action,
            cl.next_action_date,
            u.name AS writer_name,
            cl.created_at
        FROM consult_logs cl
        JOIN users u
            ON cl.user_id = u.id
        WHERE cl.customer_id = ?
        ORDER BY cl.consult_date DESC, cl.created_at DESC
    """, (customer_id,))

    rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]


def get_month_next_actions(user, year, month):
    ensure_consult_columns()

    start_date = f"{year:04d}-{month:02d}-01"

    if month == 12:
        end_date = f"{year + 1:04d}-01-01"
    else:
        end_date = f"{year:04d}-{month + 1:02d}-01"

    conn = get_conn()
    cur = conn.cursor()

    if user["role"] == "admin":
        cur.execute("""
            SELECT
                cl.id,
                cl.customer_id,
                cl.next_action_date,
                cl.next_action,
                c.name AS customer_name,
                c.phone AS customer_phone,
                u.name AS owner_name
            FROM consult_logs cl
            JOIN customers c
                ON cl.customer_id = c.id
            JOIN users u
                ON c.owner_user_id = u.id
            WHERE cl.next_action_date >= ?
              AND cl.next_action_date < ?
            ORDER BY cl.next_action_date ASC
        """, (start_date, end_date))
    else:
        cur.execute("""
            SELECT
                cl.id,
                cl.customer_id,
                cl.next_action_date,
                cl.next_action,
                c.name AS customer_name,
                c.phone AS customer_phone,
                u.name AS owner_name
            FROM consult_logs cl
            JOIN customers c
                ON cl.customer_id = c.id
            JOIN users u
                ON c.owner_user_id = u.id
            WHERE cl.next_action_date >= ?
              AND cl.next_action_date < ?
              AND c.owner_user_id = ?
            ORDER BY cl.next_action_date ASC
        """, (start_date, end_date, user["id"]))

    rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]