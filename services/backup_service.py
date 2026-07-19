"""SQLite 数据库在线备份、校验与恢复。"""

import sqlite3
from datetime import datetime
from pathlib import Path

from database.db import get_connection
from utils.paths import BACKUP_DIR, DATABASE_FILE


def verify_database(path: Path) -> bool:
    if not path.is_file():
        return False
    connection = sqlite3.connect(path)
    try:
        result = connection.execute("PRAGMA integrity_check").fetchone()
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        return result is not None and result[0] == "ok" and {"users", "books", "loans"}.issubset(tables)
    except sqlite3.DatabaseError:
        return False
    finally:
        connection.close()


def create_backup(destination_dir: Path | None = None) -> Path:
    target_dir = destination_dir or BACKUP_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"library-{datetime.now():%Y%m%d-%H%M%S-%f}.db"
    source = get_connection(); backup = sqlite3.connect(target)
    try:
        source.backup(backup)
    finally:
        backup.close(); source.close()
    if not verify_database(target):
        target.unlink(missing_ok=True)
        raise ValueError("数据库备份校验失败")
    return target


def restore_backup(backup_file: Path) -> Path:
    backup_file = backup_file.resolve()
    if not verify_database(backup_file):
        raise ValueError("所选文件不是有效的图书管理系统备份")
    safety_backup = create_backup()
    source = sqlite3.connect(backup_file); destination = sqlite3.connect(DATABASE_FILE)
    try:
        source.backup(destination)
    finally:
        destination.close(); source.close()
    if not verify_database(DATABASE_FILE):
        raise ValueError("恢复后的数据库校验失败，请使用自动安全备份恢复")
    return safety_backup


def create_daily_backup_if_needed() -> Path | None:
    """每天首次启动时自动备份一次。"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    prefix = f"library-{datetime.now():%Y%m%d}-"
    if any(path.name.startswith(prefix) for path in BACKUP_DIR.glob("library-*.db")):
        return None
    return create_backup()
