from utils.db import get_conn


def ensure_personal_schedule_table():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS personal_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            schedule_date TEXT NOT NULL,
            title TEXT NOT NULL,
            memo TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


def add_personal_schedule(user_id, schedule_date, title, memo=""):
    ensure_personal_schedule_table()

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO personal_schedules
        (user_id, schedule_date, title, memo)
        VALUES (?, ?, ?, ?)
    """, (
        user_id,
        schedule_date,
        title,
        memo
    ))

    conn.commit()
    conn.close()


def delete_personal_schedule(schedule_id, user):
    ensure_personal_schedule_table()

    conn = get_conn()
    cur = conn.cursor()

    if user["role"] == "admin":
        cur.execute("""
            DELETE FROM personal_schedules
            WHERE id = ?
        """, (schedule_id,))
    else:
        cur.execute("""
            DELETE FROM personal_schedules
            WHERE id = ?
              AND user_id = ?
        """, (schedule_id, user["id"]))

    conn.commit()
    conn.close()


def get_month_personal_schedules(user, year, month):
    ensure_personal_schedule_table()

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
                ps.id,
                ps.user_id,
                ps.schedule_date,
                ps.title,
                ps.memo,
                u.name AS owner_name
            FROM personal_schedules ps
            JOIN users u
                ON ps.user_id = u.id
            WHERE ps.schedule_date >= ?
              AND ps.schedule_date < ?
            ORDER BY ps.schedule_date ASC
        """, (start_date, end_date))
    else:
        cur.execute("""
            SELECT
                ps.id,
                ps.user_id,
                ps.schedule_date,
                ps.title,
                ps.memo,
                u.name AS owner_name
            FROM personal_schedules ps
            JOIN users u
                ON ps.user_id = u.id
            WHERE ps.schedule_date >= ?
              AND ps.schedule_date < ?
              AND ps.user_id = ?
            ORDER BY ps.schedule_date ASC
        """, (start_date, end_date, user["id"]))

    rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]