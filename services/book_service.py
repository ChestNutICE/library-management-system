"""图书新增、查询、修改、启停和库存业务。"""

import sqlite3
import shutil
from pathlib import Path
from uuid import uuid4

from database.db import get_connection, transaction
from services.log_service import write_log
from utils.validators import require_isbn, require_non_negative_int, require_text
from utils.paths import DATA_DIR


def _store_cover(source: str) -> str:
    if not source.strip(): return ""
    path=Path(source)
    if not path.is_file(): raise ValueError("封面图片文件不存在")
    cover_dir=DATA_DIR/"covers";cover_dir.mkdir(parents=True,exist_ok=True)
    try:
        if path.resolve().parent==cover_dir.resolve(): return str(path.resolve())
    except OSError: pass
    target=cover_dir/f"{uuid4().hex}{path.suffix.lower()}";shutil.copy2(path,target);return str(target)


def add_book(isbn: str, title: str, author: str, total_count: int = 1,
             category_id: int | None = None, publisher: str = "", location: str = "",
             operator_id: int | None = None, cover_path: str = "") -> int:
    clean_isbn = require_isbn(isbn); clean_title = require_text(title, "书名")
    clean_author = require_text(author, "作者"); count = require_non_negative_int(total_count, "总库存")
    try:
        with transaction() as connection:
            cursor = connection.execute(
                """INSERT INTO books(isbn,title,author,publisher,category_id,total_count,
                   available_count,location,cover_path) VALUES(?,?,?,?,?,?,?,?,?)""",
                (clean_isbn, clean_title, clean_author, publisher.strip(), category_id,
                 count, count, location.strip(), _store_cover(cover_path)),
            )
            book_id = int(cursor.lastrowid)
            write_log(connection, operator_id, "book.add", f"新增图书：{clean_title}，ISBN：{clean_isbn}")
            return book_id
    except sqlite3.IntegrityError as exc:
        if "books.isbn" in str(exc): raise ValueError("ISBN已存在") from exc
        raise


def get_book(book_id: int) -> dict | None:
    connection = get_connection()
    try:
        row = connection.execute("SELECT * FROM books WHERE id = ?", (book_id,)).fetchone()
        return dict(row) if row else None
    finally: connection.close()


def list_books(keyword: str = "", include_inactive: bool = False,
               category_id: int | None = None) -> list[dict]:
    conditions: list[str] = []; params: list[object] = []
    if keyword.strip():
        conditions.append("(b.title LIKE ? OR b.author LIKE ? OR b.isbn LIKE ?)")
        like = f"%{keyword.strip()}%"; params.extend((like, like, like))
    if not include_inactive: conditions.append("b.status = 1")
    if category_id is not None: conditions.append("b.category_id = ?"); params.append(category_id)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    connection = get_connection()
    try:
        rows = connection.execute(
            f"""SELECT b.*, c.name AS category_name FROM books b
                LEFT JOIN categories c ON c.id = b.category_id {where} ORDER BY b.id DESC""", params
        ).fetchall()
        return [dict(row) for row in rows]
    finally: connection.close()


def update_book(book_id: int, *, title: str, author: str, total_count: int,
                publisher: str = "", location: str = "", category_id: int | None = None,
                cover_path: str = "", operator_id: int | None = None) -> None:
    clean_title = require_text(title, "书名"); clean_author = require_text(author, "作者")
    count = require_non_negative_int(total_count, "总库存")
    with transaction() as connection:
        current = connection.execute("SELECT total_count,available_count FROM books WHERE id=?", (book_id,)).fetchone()
        if current is None: raise ValueError("图书不存在")
        borrowed = current["total_count"] - current["available_count"]
        if count < borrowed: raise ValueError("新总库存不能小于当前借出数量")
        connection.execute(
            """UPDATE books SET title=?,author=?,publisher=?,total_count=?,available_count=?,
               location=?,category_id=?,cover_path=? WHERE id=?""",
            (clean_title, clean_author, publisher.strip(), count, count - borrowed,
             location.strip(), category_id, _store_cover(cover_path), book_id),
        )
        write_log(connection, operator_id, "book.update", f"修改图书 ID：{book_id}，书名：{clean_title}")


def set_book_active(book_id: int, active: bool, operator_id: int | None = None) -> None:
    with transaction() as connection:
        cursor = connection.execute("UPDATE books SET status=? WHERE id=?", (int(active), book_id))
        if cursor.rowcount == 0: raise ValueError("图书不存在")
        action = "book.activate" if active else "book.deactivate"
        write_log(connection, operator_id, action, f"{'启用' if active else '停用'}图书 ID：{book_id}")


def deactivate_book(book_id: int, operator_id: int | None = None) -> None:
    set_book_active(book_id, False, operator_id)


def activate_book(book_id: int, operator_id: int | None = None) -> None:
    set_book_active(book_id, True, operator_id)
