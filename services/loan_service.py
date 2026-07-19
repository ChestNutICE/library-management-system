"""借书、还书、逾期与借阅记录查询。"""

from datetime import date

from config import FINE_PER_DAY, MAX_ACTIVE_LOANS
from database.db import get_connection, transaction
from services.log_service import write_log
from utils.date_utils import default_due_date, today


ACTIVE_STATUSES = ("borrowed", "overdue")


def _refresh_overdue(connection, current_date: date) -> None:
    connection.execute(
        """UPDATE loans SET status = 'overdue'
           WHERE status = 'borrowed' AND due_date < ?""",
        (current_date.isoformat(),),
    )


def borrow_book(user_id: int, book_id: int, borrow_date: date | None = None,
                operator_id: int | None = None) -> int:
    borrowed_on = borrow_date or today()
    due_on = default_due_date(borrowed_on)
    with transaction() as connection:
        _refresh_overdue(connection, borrowed_on)
        reader = connection.execute(
            "SELECT status FROM users WHERE id = ? AND role = 'reader'", (user_id,)
        ).fetchone()
        if reader is None:
            raise ValueError("读者不存在")
        if reader["status"] != 1:
            raise ValueError("读者账户已停用")

        book = connection.execute(
            "SELECT status, available_count FROM books WHERE id = ?", (book_id,)
        ).fetchone()
        if book is None:
            raise ValueError("图书不存在")
        if book["status"] != 1:
            raise ValueError("图书已停用")
        active_count = connection.execute(
            "SELECT COUNT(*) FROM loans WHERE user_id = ? AND status IN ('borrowed', 'overdue')",
            (user_id,),
        ).fetchone()[0]
        if active_count >= MAX_ACTIVE_LOANS:
            raise ValueError(f"每名读者最多同时借阅 {MAX_ACTIVE_LOANS} 本图书")
        duplicate = connection.execute(
            """SELECT 1 FROM loans WHERE user_id = ? AND book_id = ?
               AND status IN ('borrowed', 'overdue')""",
            (user_id, book_id),
        ).fetchone()
        if duplicate:
            raise ValueError("该读者尚未归还同一本图书")
        if book["available_count"] <= 0:
            raise ValueError("该图书暂无可借库存")

        cursor = connection.execute(
            """INSERT INTO loans(user_id, book_id, borrow_date, due_date, status)
               VALUES (?, ?, ?, ?, 'borrowed')""",
            (user_id, book_id, borrowed_on.isoformat(), due_on.isoformat()),
        )
        connection.execute(
            "UPDATE books SET available_count = available_count - 1 WHERE id = ?",
            (book_id,),
        )
        write_log(connection, operator_id, "loan.borrow", f"读者 ID：{user_id} 借阅图书 ID：{book_id}，应还：{due_on.isoformat()}")
        return int(cursor.lastrowid)


def return_book(loan_id: int, return_date: date | None = None,
                operator_id: int | None = None) -> float:
    returned_on = return_date or today()
    with transaction() as connection:
        loan = connection.execute(
            "SELECT book_id, due_date, status FROM loans WHERE id = ?", (loan_id,)
        ).fetchone()
        if loan is None:
            raise ValueError("借阅记录不存在")
        if loan["status"] == "returned":
            raise ValueError("该图书已经归还")
        overdue_days = max(0, (returned_on - date.fromisoformat(loan["due_date"])).days)
        fine = round(overdue_days * FINE_PER_DAY, 2)
        connection.execute(
            """UPDATE loans SET return_date = ?, status = 'returned', fine = ?
               WHERE id = ?""",
            (returned_on.isoformat(), fine, loan_id),
        )
        connection.execute(
            "UPDATE books SET available_count = available_count + 1 WHERE id = ?",
            (loan["book_id"],),
        )
        write_log(connection, operator_id, "loan.return", f"归还记录 ID：{loan_id}，费用：{fine:.2f} 元")
        return fine


def renew_loan(loan_id: int, operator_id: int | None = None,
               current_date: date | None = None) -> str:
    """未逾期借阅可续借一次，期限从原应还日延长 30 天。"""
    check_date = current_date or today()
    with transaction() as connection:
        _refresh_overdue(connection, check_date)
        loan = connection.execute(
            "SELECT due_date,status,renew_count FROM loans WHERE id=?", (loan_id,)
        ).fetchone()
        if loan is None: raise ValueError("借阅记录不存在")
        if loan["status"] == "returned": raise ValueError("已归还记录不能续借")
        if loan["status"] == "overdue": raise ValueError("逾期图书不能续借")
        if loan["renew_count"] >= 1: raise ValueError("每条借阅记录只能续借一次")
        new_due = default_due_date(date.fromisoformat(loan["due_date"]))
        connection.execute(
            "UPDATE loans SET due_date=?,renew_count=renew_count+1 WHERE id=?",
            (new_due.isoformat(), loan_id),
        )
        write_log(connection, operator_id, "loan.renew", f"续借记录 ID：{loan_id}，新应还日：{new_due.isoformat()}")
        return new_due.isoformat()


def list_loans(keyword: str = "", status: str = "all", user_id: int | None = None,
               current_date: date | None = None) -> list[dict]:
    with transaction() as connection:
        _refresh_overdue(connection, current_date or today())
    conditions: list[str] = []
    params: list[object] = []
    if keyword.strip():
        conditions.append("(u.username LIKE ? OR u.real_name LIKE ? OR b.title LIKE ? OR b.isbn LIKE ?)")
        like = f"%{keyword.strip()}%"; params.extend((like, like, like, like))
    if status != "all":
        conditions.append("l.status = ?"); params.append(status)
    if user_id is not None:
        conditions.append("l.user_id = ?"); params.append(user_id)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    connection = get_connection()
    try:
        rows = connection.execute(
                f"""SELECT l.id, l.user_id, l.book_id, u.username, u.real_name, u.phone,
                       b.isbn, b.title, l.borrow_date, l.due_date,
                       l.return_date, l.status, l.fine, l.renew_count
                FROM loans l JOIN users u ON u.id = l.user_id
                JOIN books b ON b.id = l.book_id
                {where} ORDER BY l.id DESC""",
            params,
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()
