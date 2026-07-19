"""读者账户的新增、查询、修改与停用业务。"""

import sqlite3

from database.db import get_connection, transaction
from services.log_service import write_log
from utils.password import hash_password
from utils.validators import require_text, validate_phone


def add_reader(username: str, password: str, real_name: str, phone: str = "", operator_id: int | None = None) -> int:
    clean_username = require_text(username, "用户名")
    clean_name = require_text(real_name, "姓名")
    if len(password) < 6:
        raise ValueError("密码至少需要 6 位")
    try:
        with transaction() as connection:
            clean_phone = validate_phone(phone)
            cursor = connection.execute(
                """INSERT INTO users(username, password_hash, real_name, role, phone)
                   VALUES (?, ?, ?, 'reader', ?)""",
                (clean_username, hash_password(password), clean_name, clean_phone),
            )
            reader_id = int(cursor.lastrowid)
            write_log(connection, operator_id, "reader.add", f"新增读者：{clean_name}（{clean_username}）")
            return reader_id
    except sqlite3.IntegrityError as exc:
        if "users.username" in str(exc):
            raise ValueError("用户名已存在") from exc
        raise


def get_reader(reader_id: int) -> dict | None:
    connection = get_connection()
    try:
        row = connection.execute(
            """SELECT id, username, real_name, phone, status, created_at
               FROM users WHERE id = ? AND role = 'reader'""",
            (reader_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        connection.close()


def list_readers(keyword: str = "", include_inactive: bool = False) -> list[dict]:
    conditions = ["role = 'reader'"]
    params: list[object] = []
    if keyword.strip():
        conditions.append("(username LIKE ? OR real_name LIKE ? OR phone LIKE ?)")
        like = f"%{keyword.strip()}%"
        params.extend((like, like, like))
    if not include_inactive:
        conditions.append("status = 1")
    connection = get_connection()
    try:
        rows = connection.execute(
            f"""SELECT id, username, real_name, phone, status, created_at
                FROM users WHERE {' AND '.join(conditions)} ORDER BY id DESC""",
            params,
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def update_reader(reader_id: int, *, real_name: str, phone: str = "", operator_id: int | None = None) -> None:
    clean_name = require_text(real_name, "姓名")
    with transaction() as connection:
        cursor = connection.execute(
            """UPDATE users SET real_name = ?, phone = ?
               WHERE id = ? AND role = 'reader'""",
            (clean_name, validate_phone(phone), reader_id),
        )
        if cursor.rowcount == 0:
            raise ValueError("读者不存在")
        write_log(connection, operator_id, "reader.update", f"修改读者 ID：{reader_id}，姓名：{clean_name}")


def deactivate_reader(reader_id: int, operator_id: int | None = None) -> None:
    with transaction() as connection:
        active_loans = connection.execute(
            """SELECT COUNT(*) FROM loans
               WHERE user_id = ? AND status IN ('borrowed', 'overdue')""",
            (reader_id,),
        ).fetchone()[0]
        if active_loans:
            raise ValueError("该读者仍有未归还图书，不能停用")
        cursor = connection.execute(
            "UPDATE users SET status = 0 WHERE id = ? AND role = 'reader'",
            (reader_id,),
        )
        if cursor.rowcount == 0:
            raise ValueError("读者不存在")
        write_log(connection, operator_id, "reader.deactivate", f"停用读者 ID：{reader_id}")
