"""登录与账户验证。"""

from database.db import get_connection, transaction
from models.user import User
from utils.password import hash_password, verify_password


def authenticate(username: str, password: str) -> User | None:
    connection = get_connection()
    try:
        row = connection.execute(
            """
            SELECT id, username, password_hash, real_name, role, phone, status
            FROM users WHERE username = ?
            """,
            (username.strip(),),
        ).fetchone()
    finally:
        connection.close()

    if row is None or row["status"] != 1:
        return None
    if not verify_password(password, row["password_hash"]):
        return None
    return User(
        id=row["id"], username=row["username"], real_name=row["real_name"],
        role=row["role"], phone=row["phone"], status=row["status"],
    )


def change_password(user_id: int, current_password: str, new_password: str) -> None:
    if len(new_password) < 6:
        raise ValueError("新密码至少需要 6 位")
    with transaction() as connection:
        row = connection.execute(
            "SELECT password_hash, status FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if row is None or row["status"] != 1:
            raise ValueError("账户不存在或已停用")
        if not verify_password(current_password, row["password_hash"]):
            raise ValueError("原密码不正确")
        if verify_password(new_password, row["password_hash"]):
            raise ValueError("新密码不能与原密码相同")
        connection.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hash_password(new_password), user_id),
        )
