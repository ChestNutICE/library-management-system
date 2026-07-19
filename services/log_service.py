"""操作日志写入与查询。"""

from database.db import get_connection


def write_log(connection, operator_id: int | None, action: str, details: str = "") -> None:
    """使用调用方事务写日志，确保日志与业务数据同时提交。"""
    connection.execute(
        "INSERT INTO operation_logs(operator_id, action, details) VALUES (?, ?, ?)",
        (operator_id, action, details),
    )


def list_logs(keyword: str = "", action: str = "all", limit: int = 500) -> list[dict]:
    conditions: list[str] = []
    params: list[object] = []
    if keyword.strip():
        conditions.append("(COALESCE(u.username, '') LIKE ? OR COALESCE(u.real_name, '') LIKE ? OR COALESCE(l.details, '') LIKE ?)")
        like = f"%{keyword.strip()}%"; params.extend((like, like, like))
    if action != "all":
        conditions.append("l.action = ?"); params.append(action)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.append(limit)
    connection = get_connection()
    try:
        rows = connection.execute(
            f"""SELECT l.id, l.operator_id, COALESCE(u.username, 'system') AS username,
                       COALESCE(u.real_name, '系统') AS real_name,
                       l.action, l.details, l.created_at
                FROM operation_logs l LEFT JOIN users u ON u.id = l.operator_id
                {where} ORDER BY l.id DESC LIMIT ?""",
            params,
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()
