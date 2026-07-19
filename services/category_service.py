"""图书分类维护。"""

import sqlite3

from database.db import get_connection, transaction
from services.log_service import write_log
from utils.validators import require_text


def list_categories() -> list[dict]:
    connection = get_connection()
    try:
        rows = connection.execute("SELECT id, name FROM categories ORDER BY name").fetchall()
        return [dict(row) for row in rows]
    finally: connection.close()


def add_category(name: str, operator_id: int | None = None) -> int:
    clean = require_text(name, "分类名称")
    try:
        with transaction() as connection:
            cursor = connection.execute("INSERT INTO categories(name) VALUES (?)", (clean,))
            category_id = int(cursor.lastrowid)
            write_log(connection, operator_id, "category.add", f"新增分类：{clean}")
            return category_id
    except sqlite3.IntegrityError as exc:
        raise ValueError("分类名称已存在") from exc


def rename_category(category_id: int, name: str, operator_id: int | None = None) -> None:
    clean = require_text(name, "分类名称")
    try:
        with transaction() as connection:
            cursor = connection.execute("UPDATE categories SET name = ? WHERE id = ?", (clean, category_id))
            if cursor.rowcount == 0: raise ValueError("分类不存在")
            write_log(connection, operator_id, "category.rename", f"修改分类 ID：{category_id}，名称：{clean}")
    except sqlite3.IntegrityError as exc:
        raise ValueError("分类名称已存在") from exc


def delete_category(category_id: int, operator_id: int | None = None) -> None:
    with transaction() as connection:
        used = connection.execute("SELECT COUNT(*) FROM books WHERE category_id = ?", (category_id,)).fetchone()[0]
        if used: raise ValueError("该分类仍有图书，不能删除")
        cursor = connection.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        if cursor.rowcount == 0: raise ValueError("分类不存在")
        write_log(connection, operator_id, "category.delete", f"删除分类 ID：{category_id}")
