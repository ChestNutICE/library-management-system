"""管理员子账号和细粒度功能权限。"""

import sqlite3
from database.db import get_connection, transaction
from services.log_service import write_log
from utils.password import hash_password
from utils.validators import require_text

PERMISSION_KEYS=("manage_books","manage_readers","manage_loans","view_reports")


def get_permissions(user_id:int) -> dict[str,bool]:
    connection=get_connection()
    try:row=connection.execute("SELECT * FROM user_permissions WHERE user_id=?",(user_id,)).fetchone()
    finally:connection.close()
    return {key:bool(row[key]) if row else False for key in PERMISSION_KEYS}


def list_staff() -> list[dict]:
    connection=get_connection()
    try:
        rows=connection.execute("""SELECT u.id,u.username,u.real_name,u.status,
          COALESCE(p.manage_books,0) manage_books,COALESCE(p.manage_readers,0) manage_readers,
          COALESCE(p.manage_loans,0) manage_loans,COALESCE(p.view_reports,0) view_reports
          FROM users u LEFT JOIN user_permissions p ON p.user_id=u.id WHERE u.role='admin' ORDER BY u.id""").fetchall()
        return [dict(row) for row in rows]
    finally:connection.close()


def add_staff(username:str,password:str,real_name:str,permissions:dict[str,bool],operator_id:int)->int:
    if len(password)<6:raise ValueError("密码至少需要 6 位")
    try:
        with transaction() as connection:
            cursor=connection.execute("INSERT INTO users(username,password_hash,real_name,role) VALUES(?,?,?,'admin')",(require_text(username,"用户名"),hash_password(password),require_text(real_name,"姓名")))
            staff_id=int(cursor.lastrowid);values=[int(permissions.get(key,False)) for key in PERMISSION_KEYS]
            connection.execute("INSERT INTO user_permissions(user_id,manage_books,manage_readers,manage_loans,view_reports) VALUES(?,?,?,?,?)",(staff_id,*values))
            write_log(connection,operator_id,"staff.add",f"新增管理员子账号：{username}");return staff_id
    except sqlite3.IntegrityError as exc:raise ValueError("用户名已存在") from exc


def update_permissions(user_id:int,permissions:dict[str,bool],operator_id:int)->None:
    if user_id==operator_id:raise ValueError("不能修改当前登录账号自身的权限")
    values=[int(permissions.get(key,False)) for key in PERMISSION_KEYS]
    with transaction() as connection:
        connection.execute("""INSERT INTO user_permissions(user_id,manage_books,manage_readers,manage_loans,view_reports)
          VALUES(?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET manage_books=excluded.manage_books,
          manage_readers=excluded.manage_readers,manage_loans=excluded.manage_loans,view_reports=excluded.view_reports""",(user_id,*values))
        write_log(connection,operator_id,"staff.permissions",f"修改管理员权限 ID：{user_id}")
