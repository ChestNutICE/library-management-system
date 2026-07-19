from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

import database.db as db_module
from database.init_db import initialize_database
from services.book_service import activate_book, add_book, deactivate_book, get_book, list_books
from services.category_service import add_category, delete_category, list_categories, rename_category
from services.export_service import read_xlsx, write_xlsx
from services.loan_service import borrow_book, list_loans, renew_loan
from services.reader_service import activate_reader, add_reader, deactivate_reader, list_readers
from services.reminder_service import due_reminders
from utils.paths import DATA_DIR


@pytest.fixture()
def isolated_database(monkeypatch):
    database_file=DATA_DIR/f"test-library-{uuid4().hex}.db"; monkeypatch.setattr(db_module,"DATABASE_FILE",database_file)
    initialize_database(); yield database_file; database_file.unlink(missing_ok=True)


def test_categories_filter_and_used_category_protection(isolated_database):
    category=add_category("人工智能"); rename_category(category,"AI")
    book=add_book("9787000000001","机器学习","作者",category_id=category)
    assert list_books(category_id=category)[0]["id"]==book
    with pytest.raises(ValueError,match="仍有图书"):delete_category(category)
    assert any(row["name"]=="AI" for row in list_categories())


def test_book_and_reader_can_be_reactivated(isolated_database):
    book=add_book("9787000000001","图书","作者"); reader=add_reader("reader001","secret12","张三")
    deactivate_book(book); deactivate_reader(reader)
    assert list_books()==[] and list_readers()==[]
    activate_book(book); activate_reader(reader)
    assert list_books()[0]["id"]==book and list_readers()[0]["id"]==reader


def test_renew_once_and_reminder(isolated_database):
    reader=add_reader("reader001","secret12","张三"); book=add_book("9787000000001","图书","作者")
    borrowed=date.today()-timedelta(days=28); loan=borrow_book(reader,book,borrowed)
    old_due=list_loans(user_id=reader)[0]["due_date"]; new_due=renew_loan(loan,current_date=date.today())
    assert date.fromisoformat(new_due)==date.fromisoformat(old_due)+timedelta(days=30)
    with pytest.raises(ValueError,match="只能续借一次"):renew_loan(loan,current_date=date.today())
    assert due_reminders(40,reader)[0]["renew_count"]==1


def test_xlsx_round_trip_without_third_party_dependency(isolated_database):
    path=DATA_DIR/f"test-export-{uuid4().hex}.xlsx"
    try:
        write_xlsx(path,["ISBN","书名"],[["9787000000001","测试图书"]])
        assert read_xlsx(path)==[{"ISBN":"9787000000001","书名":"测试图书"}]
    finally:path.unlink(missing_ok=True)
