from uuid import uuid4

import pytest

import database.db as db_module
import services.backup_service as backup_module
from database.init_db import initialize_database
from services.backup_service import create_backup, restore_backup, verify_database
from services.book_service import add_book, list_books
from utils.paths import DATA_DIR


@pytest.fixture()
def isolated_database(monkeypatch):
    token = uuid4().hex
    database_file = DATA_DIR / f"test-library-{token}.db"
    backup_dir = DATA_DIR / f"test-backups-{token}"
    monkeypatch.setattr(db_module, "DATABASE_FILE", database_file)
    monkeypatch.setattr(backup_module, "DATABASE_FILE", database_file)
    monkeypatch.setattr(backup_module, "BACKUP_DIR", backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    initialize_database()
    yield backup_dir
    database_file.unlink(missing_ok=True)
    for file in backup_dir.glob("*"): file.unlink(missing_ok=True)
    if backup_dir.exists():
        backup_dir.rmdir()


def test_backup_and_restore_round_trip(isolated_database) -> None:
    add_book("9787000000001", "备份前图书", "作者")
    backup = create_backup()
    assert verify_database(backup)
    add_book("9787000000002", "备份后图书", "作者")
    assert len(list_books()) == 2
    safety = restore_backup(backup)
    assert verify_database(safety)
    assert [book["title"] for book in list_books()] == ["备份前图书"]


def test_invalid_backup_is_rejected(isolated_database) -> None:
    invalid = isolated_database / "invalid.db"
    invalid.write_text("not sqlite", encoding="utf-8")
    assert not verify_database(invalid)
    with pytest.raises(ValueError, match="不是有效"):
        restore_backup(invalid)
