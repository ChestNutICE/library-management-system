from uuid import uuid4

import pytest

import database.db as db_module
from database.init_db import initialize_database
from services.auth_service import authenticate
from services.reader_service import add_reader, deactivate_reader, get_reader, list_readers, update_reader
from utils.paths import DATA_DIR


@pytest.fixture()
def isolated_database(monkeypatch):
    database_file = DATA_DIR / f"test-library-{uuid4().hex}.db"
    monkeypatch.setattr(db_module, "DATABASE_FILE", database_file)
    initialize_database(); yield database_file; database_file.unlink(missing_ok=True)


def test_reader_crud_and_login(isolated_database) -> None:
    reader_id = add_reader("reader001", "secret12", "张同学", "13800000000")
    assert authenticate("reader001", "secret12").real_name == "张同学"
    assert list_readers("张同学")[0]["id"] == reader_id
    update_reader(reader_id, real_name="张三", phone="13900000000")
    assert get_reader(reader_id)["phone"] == "13900000000"
    deactivate_reader(reader_id)
    assert list_readers() == []
    assert authenticate("reader001", "secret12") is None


def test_duplicate_username_and_short_password(isolated_database) -> None:
    add_reader("reader001", "secret12", "甲")
    with pytest.raises(ValueError, match="用户名已存在"):
        add_reader("reader001", "secret12", "乙")
    with pytest.raises(ValueError, match="至少需要 6 位"):
        add_reader("reader002", "123", "丙")
