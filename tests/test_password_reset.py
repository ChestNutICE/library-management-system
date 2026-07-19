from uuid import uuid4

import pytest

import database.db as db_module
from database.init_db import initialize_database
from services.auth_service import authenticate
from services.log_service import list_logs
from services.reader_service import add_reader, reset_reader_password
from utils.paths import DATA_DIR


@pytest.fixture()
def isolated_database(monkeypatch):
    database_file = DATA_DIR / f"test-library-{uuid4().hex}.db"
    monkeypatch.setattr(db_module, "DATABASE_FILE", database_file)
    initialize_database(); yield; database_file.unlink(missing_ok=True)


def get_admin_id() -> int:
    connection = db_module.get_connection()
    try: return int(connection.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()[0])
    finally: connection.close()


def test_admin_can_reset_reader_password(isolated_database) -> None:
    admin_id = get_admin_id()
    reader_id = add_reader("reader001", "oldpass8", "张三", operator_id=admin_id)
    reset_reader_password(reader_id, "newpass9", admin_id)
    assert authenticate("reader001", "oldpass8") is None
    assert authenticate("reader001", "newpass9") is not None
    log = list_logs(action="reader.reset_password")[0]
    assert log["operator_id"] == admin_id
    assert "reader001" in log["details"]
    assert "newpass9" not in log["details"]


def test_reset_rejects_short_password(isolated_database) -> None:
    admin_id = get_admin_id()
    reader_id = add_reader("reader001", "oldpass8", "张三", operator_id=admin_id)
    with pytest.raises(ValueError, match="至少需要 6 位"):
        reset_reader_password(reader_id, "123", admin_id)
    assert authenticate("reader001", "oldpass8") is not None


def test_reader_cannot_reset_another_reader_password(isolated_database) -> None:
    admin_id = get_admin_id()
    first = add_reader("reader001", "oldpass8", "张三", operator_id=admin_id)
    second = add_reader("reader002", "oldpass9", "李四", operator_id=admin_id)
    with pytest.raises(PermissionError, match="只有有效管理员"):
        reset_reader_password(second, "newpass9", first)
    assert authenticate("reader002", "oldpass9") is not None
