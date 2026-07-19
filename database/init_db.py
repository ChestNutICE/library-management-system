"""数据库建表和初始数据。"""

from config import DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_USERNAME
from database.db import transaction
from utils.password import hash_password


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    real_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('admin', 'reader')),
    phone TEXT,
    status INTEGER NOT NULL DEFAULT 1 CHECK (status IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    isbn TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    publisher TEXT,
    publish_date TEXT,
    category_id INTEGER,
    price REAL NOT NULL DEFAULT 0 CHECK (price >= 0),
    total_count INTEGER NOT NULL DEFAULT 1 CHECK (total_count >= 0),
    available_count INTEGER NOT NULL DEFAULT 1,
    location TEXT,
    description TEXT,
    status INTEGER NOT NULL DEFAULT 1 CHECK (status IN (0, 1)),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id),
    CHECK (available_count >= 0 AND available_count <= total_count)
);

CREATE TABLE IF NOT EXISTS loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    book_id INTEGER NOT NULL,
    borrow_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    return_date TEXT,
    status TEXT NOT NULL DEFAULT 'borrowed'
        CHECK (status IN ('borrowed', 'returned', 'overdue')),
    fine REAL NOT NULL DEFAULT 0 CHECK (fine >= 0),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (book_id) REFERENCES books(id)
);

CREATE TABLE IF NOT EXISTS operation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operator_id INTEGER,
    action TEXT NOT NULL,
    details TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (operator_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS user_permissions (
    user_id INTEGER PRIMARY KEY,
    manage_books INTEGER NOT NULL DEFAULT 0 CHECK (manage_books IN (0, 1)),
    manage_readers INTEGER NOT NULL DEFAULT 0 CHECK (manage_readers IN (0, 1)),
    manage_loans INTEGER NOT NULL DEFAULT 0 CHECK (manage_loans IN (0, 1)),
    view_reports INTEGER NOT NULL DEFAULT 0 CHECK (view_reports IN (0, 1)),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""

CATEGORIES = ("计算机", "文学", "历史", "经济", "科学", "其他")


def initialize_database() -> None:
    with transaction() as connection:
        connection.executescript(SCHEMA)
        book_columns = {row["name"] for row in connection.execute("PRAGMA table_info(books)")}
        if "cover_path" not in book_columns:
            connection.execute("ALTER TABLE books ADD COLUMN cover_path TEXT")
        loan_columns = {row["name"] for row in connection.execute("PRAGMA table_info(loans)")}
        if "renew_count" not in loan_columns:
            connection.execute("ALTER TABLE loans ADD COLUMN renew_count INTEGER NOT NULL DEFAULT 0")
        connection.executemany(
            "INSERT OR IGNORE INTO categories(name) VALUES (?)",
            [(name,) for name in CATEGORIES],
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO users
                (username, password_hash, real_name, role)
            VALUES (?, ?, ?, 'admin')
            """,
            (
                DEFAULT_ADMIN_USERNAME,
                hash_password(DEFAULT_ADMIN_PASSWORD),
                "系统管理员",
            ),
        )
        connection.execute(
            """INSERT OR IGNORE INTO user_permissions
               (user_id, manage_books, manage_readers, manage_loans, view_reports)
               SELECT id, 1, 1, 1, 1 FROM users WHERE username = ?""",
            (DEFAULT_ADMIN_USERNAME,),
        )
