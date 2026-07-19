from datetime import date, timedelta
from uuid import uuid4

import pytest

import database.db as db_module
from database.init_db import initialize_database
from services.auth_service import authenticate, change_password
from services.book_service import add_book
from services.loan_service import borrow_book
from services.reader_service import add_reader
from services.statistics_service import dashboard_counts, popular_books
from utils.paths import DATA_DIR


@pytest.fixture()
def isolated_database(monkeypatch):
    database_file = DATA_DIR / f"test-library-{uuid4().hex}.db"
    monkeypatch.setattr(db_module, "DATABASE_FILE", database_file)
    initialize_database(); yield; database_file.unlink(missing_ok=True)


def test_dashboard_counts_and_popular_books(isolated_database) -> None:
    reader_id = add_reader("reader001", "secret12", "张三")
    first = add_book("9787000000001", "热门图书", "作者甲", 3)
    add_book("9787000000002", "普通图书", "作者乙", 2)
    borrow_book(reader_id, first)
    counts = dashboard_counts()
    assert counts == {"book_titles": 2, "total_copies": 5, "readers": 1, "borrowed": 1, "overdue": 0}
    assert popular_books()[0]["title"] == "热门图书"
    assert popular_books()[0]["loan_count"] == 1


def test_dashboard_refreshes_overdue_count(isolated_database) -> None:
    reader_id = add_reader("reader001", "secret12", "张三")
    book_id = add_book("9787000000001", "逾期图书", "作者", 1)
    borrow_book(reader_id, book_id, date.today() - timedelta(days=31))
    counts = dashboard_counts()
    assert counts["borrowed"] == 1
    assert counts["overdue"] == 1


def test_change_password(isolated_database) -> None:
    reader_id = add_reader("reader001", "secret12", "张三")
    change_password(reader_id, "secret12", "newpass88")
    assert authenticate("reader001", "secret12") is None
    assert authenticate("reader001", "newpass88") is not None


def test_change_password_validates_input(isolated_database) -> None:
    reader_id = add_reader("reader001", "secret12", "张三")
    with pytest.raises(ValueError, match="原密码不正确"):
        change_password(reader_id, "wrong", "newpass88")
    with pytest.raises(ValueError, match="至少需要 6 位"):
        change_password(reader_id, "secret12", "123")
    with pytest.raises(ValueError, match="不能与原密码相同"):
        change_password(reader_id, "secret12", "secret12")
