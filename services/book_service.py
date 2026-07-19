"""图书基本增改查与停用业务。"""

import sqlite3

from database.db import get_connection, transaction
from services.log_service import write_log
from utils.validators import require_isbn, require_non_negative_int, require_text


def _row_to_dict(row: sqlite3.Row | None) -> dict | None:
    return dict(row) if row is not None else None


def add_book(
    isbn: str,
    title: str,
    author: str,
    total_count: int = 1,
    category_id: int | None = None,
    publisher: str = "",
    location: str = "",
    operator_id: int | None = None,
) -> int:
    clean_isbn = require_isbn(isbn)
    clean_title = require_text(title, "书名")
    clean_author = require_text(author, "作者")
    count = require_non_negative_int(total_count, "总库存")
    try:
        with transaction() as connection:
            cursor = connection.execute(
                """
                INSERT INTO books (
                    isbn, title, author, publisher, category_id,
                    total_count, available_count, location
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    clean_isbn, clean_title, clean_author, publisher.strip(),
                    category_id, count, count, location.strip(),
                ),
            )
            book_id = int(cursor.lastrowid)
            write_log(connection, operator_id, "book.add", f"新增图书：{clean_title}，ISBN：{clean_isbn}")
            return book_id
    except sqlite3.IntegrityError as exc:
        if "books.isbn" in str(exc):
            raise ValueError("ISBN已存在") from exc
        raise


def get_book(book_id: int) -> dict | None:
    connection = get_connection()
    try:
        row = connection.execute(
            "SELECT * FROM books WHERE id = ?", (book_id,)
        ).fetchone()
        return _row_to_dict(row)
    finally:
        connection.close()


def list_books(keyword: str = "", include_inactive: bool = False) -> list[dict]:
    conditions: list[str] = []
    params: list[object] = []
    if keyword.strip():
        conditions.append("(title LIKE ? OR author LIKE ? OR isbn LIKE ?)")
        like = f"%{keyword.strip()}%"
        params.extend((like, like, like))
    if not include_inactive:
        conditions.append("status = 1")
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    connection = get_connection()
    try:
        rows = connection.execute(
            f"SELECT * FROM books {where} ORDER BY id DESC", params
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def update_book(
    book_id: int,
    *,
    title: str,
    author: str,
    total_count: int,
    publisher: str = "",
    location: str = "",
    operator_id: int | None = None,
) -> None:
    clean_title = require_text(title, "书名")
    clean_author = require_text(author, "作者")
    count = require_non_negative_int(total_count, "总库存")
    with transaction() as connection:
        current = connection.execute(
            "SELECT total_count, available_count FROM books WHERE id = ?", (book_id,)
        ).fetchone()
        if current is None:
            raise ValueError("图书不存在")
        borrowed_count = current["total_count"] - current["available_count"]
        if count < borrowed_count:
            raise ValueError("新总库存不能小于当前借出数量")
        new_available = count - borrowed_count
        connection.execute(
            """
            UPDATE books
            SET title = ?, author = ?, publisher = ?, total_count = ?,
                available_count = ?, location = ?
            WHERE id = ?
            """,
            (
                clean_title, clean_author, publisher.strip(), count,
                new_available, location.strip(), book_id,
            ),
        )
        write_log(connection, operator_id, "book.update", f"修改图书 ID：{book_id}，书名：{clean_title}")


def deactivate_book(book_id: int, operator_id: int | None = None) -> None:
    with transaction() as connection:
        cursor = connection.execute(
            "UPDATE books SET status = 0 WHERE id = ?", (book_id,)
        )
        if cursor.rowcount == 0:
            raise ValueError("图书不存在")
        write_log(connection, operator_id, "book.deactivate", f"停用图书 ID：{book_id}")
