"""登录与账户验证。"""

from database.db import get_connection
from models.user import User
from utils.password import verify_password


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
