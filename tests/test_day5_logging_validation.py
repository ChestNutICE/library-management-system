from uuid import uuid4

import pytest

import database.db as db_module
from database.init_db import initialize_database
from services.book_service import add_book, deactivate_book, update_book
from services.loan_service import borrow_book, return_book
from services.log_service import list_logs
from services.reader_service import add_reader, update_reader
from utils.paths import DATA_DIR


@pytest.fixture()
def isolated_database(monkeypatch):
    database_file = DATA_DIR / f"test-library-{uuid4().hex}.db"
    monkeypatch.setattr(db_module, "DATABASE_FILE", database_file)
    initialize_database(); yield; database_file.unlink(missing_ok=True)


def admin_id() -> int:
    connection = db_module.get_connection()
    try: return int(connection.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()[0])
    finally: connection.close()


def test_complete_flow_writes_searchable_logs(isolated_database) -> None:
    operator = admin_id()
    reader = add_reader("reader001", "secret12", "张三", "13800000000", operator)
    book = add_book("978-7-000-00000-1", "日志测试图书", "作者", 2, operator_id=operator)
    update_book(book, title="修改后图书", author="作者", total_count=2, operator_id=operator)
    update_reader(reader, real_name="张三丰", phone="13900000000", operator_id=operator)
    loan = borrow_book(reader, book, operator_id=operator)
    return_book(loan, operator_id=operator)
    actions = [item["action"] for item in list_logs()]
    assert actions[:6] == ["loan.return", "loan.borrow", "reader.update", "book.update", "book.add", "reader.add"]
    assert list_logs("修改后图书", "book.update")[0]["operator_id"] == operator


def test_invalid_isbn_and_phone_are_rejected_without_log(isolated_database) -> None:
    operator = admin_id()
    with pytest.raises(ValueError, match="ISBN"):
        add_book("123", "书", "作者", operator_id=operator)
    with pytest.raises(ValueError, match="电话号码"):
        add_reader("reader001", "secret12", "张三", "abc", operator)
    assert list_logs() == []


def test_deactivate_book_writes_log(isolated_database) -> None:
    operator = admin_id(); book = add_book("9787000000001", "图书", "作者", operator_id=operator)
    deactivate_book(book, operator)
    assert list_logs(action="book.deactivate")[0]["details"].endswith(str(book))
