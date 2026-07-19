import sqlite3

import pytest

import database.db as db_module
from database.init_db import initialize_database
from services.book_service import (
    add_book,
    deactivate_book,
    get_book,
    list_books,
    update_book,
)


@pytest.fixture()
def isolated_database(tmp_path, monkeypatch):
    database_file = tmp_path / "test_library.db"
    monkeypatch.setattr(db_module, "DATABASE_FILE", database_file)
    initialize_database()
    return database_file


def test_database_initialization_is_idempotent(isolated_database) -> None:
    initialize_database()
    connection = sqlite3.connect(isolated_database)
    try:
        assert connection.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 6
    finally:
        connection.close()


def test_book_add_query_update_and_deactivate(isolated_database) -> None:
    book_id = add_book("9787111111111", "Python入门", "测试作者", 3)
    assert get_book(book_id)["available_count"] == 3
    assert list_books("Python")[0]["id"] == book_id

    update_book(
        book_id,
        title="Python程序设计",
        author="测试作者",
        total_count=5,
        publisher="测试出版社",
        location="A-01",
    )
    updated = get_book(book_id)
    assert updated["title"] == "Python程序设计"
    assert updated["total_count"] == 5
    assert updated["available_count"] == 5

    deactivate_book(book_id)
    assert list_books("Python") == []
    assert list_books("Python", include_inactive=True)[0]["status"] == 0


def test_duplicate_isbn_is_rejected(isolated_database) -> None:
    add_book("9787222222222", "第一本书", "作者甲")
    with pytest.raises(ValueError, match="ISBN已存在"):
        add_book("9787222222222", "第二本书", "作者乙")


def test_data_persists_after_reopening_connection(isolated_database) -> None:
    book_id = add_book("9787333333333", "持久化测试", "作者丙")
    assert get_book(book_id)["title"] == "持久化测试"
    assert get_book(book_id)["isbn"] == "9787333333333"
