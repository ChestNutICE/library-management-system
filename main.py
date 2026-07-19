"""图书管理系统程序入口。"""

import sys

from PySide6.QtWidgets import QApplication

from database.init_db import initialize_database
from services.backup_service import create_daily_backup_if_needed
from utils.paths import asset_path
from views.login_window import LoginWindow


def load_stylesheet(app: QApplication) -> None:
    style_file = asset_path("style.qss")
    if style_file.exists():
        app.setStyleSheet(style_file.read_text(encoding="utf-8"))


def main() -> int:
    initialize_database()
    try:
        create_daily_backup_if_needed()
    except (OSError, ValueError):
        # 自动备份失败不应阻止用户启动；管理员仍可在数据维护页手动备份。
        pass
    app = QApplication(sys.argv)
    app.setApplicationName("图书管理系统")
    load_stylesheet(app)
    window = LoginWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
