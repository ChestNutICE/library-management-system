"""首页运营统计查询。"""

from database.db import get_connection
from services.loan_service import list_loans


def dashboard_counts() -> dict[str, int]:
    # 查询借阅记录时会先刷新已到期记录的状态。
    list_loans()
    connection = get_connection()
    try:
        row = connection.execute(
            """SELECT
                (SELECT COUNT(*) FROM books WHERE status = 1) AS book_titles,
                (SELECT COALESCE(SUM(total_count), 0) FROM books WHERE status = 1) AS total_copies,
                (SELECT COUNT(*) FROM users WHERE role = 'reader' AND status = 1) AS readers,
                (SELECT COUNT(*) FROM loans WHERE status IN ('borrowed', 'overdue')) AS borrowed,
                (SELECT COUNT(*) FROM loans WHERE status = 'overdue') AS overdue"""
        ).fetchone()
        return dict(row)
    finally:
        connection.close()


def popular_books(limit: int = 5) -> list[dict]:
    connection = get_connection()
    try:
        rows = connection.execute(
            """SELECT b.id, b.title, b.author, COUNT(l.id) AS loan_count
               FROM books b LEFT JOIN loans l ON l.book_id = b.id
               GROUP BY b.id, b.title, b.author
               HAVING COUNT(l.id) > 0
               ORDER BY loan_count DESC, b.id ASC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()
