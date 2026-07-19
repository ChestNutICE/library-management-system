from uuid import uuid4
import pytest
import database.db as db_module
from database.init_db import initialize_database
from services.permission_service import add_staff,get_permissions,list_staff,update_permissions
from utils.paths import DATA_DIR

@pytest.fixture()
def isolated_database(monkeypatch):
    path=DATA_DIR/f"test-library-{uuid4().hex}.db";monkeypatch.setattr(db_module,"DATABASE_FILE",path);initialize_database();yield;path.unlink(missing_ok=True)

def admin_id():
    connection=db_module.get_connection()
    try:return int(connection.execute("SELECT id FROM users WHERE username='admin'").fetchone()[0])
    finally:connection.close()

def test_staff_permissions(isolated_database):
    admin=admin_id();staff=add_staff("librarian","secret12","馆员",{"manage_books":True,"manage_loans":True},admin)
    assert get_permissions(staff)=={"manage_books":True,"manage_readers":False,"manage_loans":True,"view_reports":False}
    update_permissions(staff,{"view_reports":True},admin);assert get_permissions(staff)["view_reports"] is True
    assert any(row["id"]==staff for row in list_staff())

def test_cannot_change_own_permissions(isolated_database):
    admin=admin_id()
    with pytest.raises(ValueError,match="自身"):update_permissions(admin,{},admin)
