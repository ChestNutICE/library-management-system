from datetime import date, timedelta
from uuid import uuid4

import pytest

import database.db as db_module
from database.init_db import initialize_database
from services.book_service import add_book, get_book
from services.loan_service import borrow_book, list_loans, return_book
from services.reader_service import add_reader
from utils.paths import DATA_DIR


@pytest.fixture()
def isolated_database(monkeypatch):
    database_file = DATA_DIR / f"test-library-{uuid4().hex}.db"
    monkeypatch.setattr(db_module, "DATABASE_FILE", database_file)
    initialize_database(); yield; database_file.unlink(missing_ok=True)


def make_reader_and_book():
    reader_id = add_reader("reader001", "secret12", "张三")
    book_id = add_book("9787000000001", "测试图书", "测试作者", 2)
    return reader_id, book_id


def test_borrow_and_return_updates_inventory(isolated_database) -> None:
    reader_id, book_id = make_reader_and_book()
    loan_id = borrow_book(reader_id, book_id, date(2026, 7, 1))
    assert get_book(book_id)["available_count"] == 1
    loan = list_loans(user_id=reader_id, current_date=date(2026, 7, 2))[0]
    assert loan["due_date"] == "2026-07-31"
    assert loan["status"] == "borrowed"
    assert return_book(loan_id, date(2026, 8, 2)) == 1.0
    assert get_book(book_id)["available_count"] == 2
    assert list_loans(status="returned")[0]["return_date"] == "2026-08-02"


def test_duplicate_and_no_inventory_are_rejected(isolated_database) -> None:
    reader_id = add_reader("reader001", "secret12", "张三")
    book_id = add_book("9787000000001", "单册图书", "作者", 1)
    borrow_book(reader_id, book_id)
    with pytest.raises(ValueError, match="尚未归还"):
        borrow_book(reader_id, book_id)
    other = add_reader("reader002", "secret12", "李四")
    with pytest.raises(ValueError, match="暂无可借库存"):
        borrow_book(other, book_id)


def test_maximum_five_active_loans(isolated_database) -> None:
    reader_id = add_reader("reader001", "secret12", "张三")
    for index in range(5):
        book_id = add_book(f"97870000000{index:02d}", f"图书{index}", "作者", 1)
        borrow_book(reader_id, book_id)
    sixth = add_book("9787999999999", "第六本", "作者", 1)
    with pytest.raises(ValueError, match="最多同时借阅 5 本"):
        borrow_book(reader_id, sixth)


def test_overdue_status_refresh(isolated_database) -> None:
    reader_id, book_id = make_reader_and_book()
    borrow_book(reader_id, book_id, date.today() - timedelta(days=31))
    assert list_loans(status="overdue")[0]["status"] == "overdue"


def test_return_twice_is_rejected(isolated_database) -> None:
    reader_id, book_id = make_reader_and_book()
    loan_id = borrow_book(reader_id, book_id)
    return_book(loan_id)
    with pytest.raises(ValueError, match="已经归还"):
        return_book(loan_id)
