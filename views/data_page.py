"""管理员数据库备份与恢复页面。"""

from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from services.backup_service import create_backup, restore_backup
from utils.paths import BACKUP_DIR, DATABASE_FILE


class DataPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self); title = QLabel("数据维护"); title.setObjectName("pageTitle")
        info = QLabel(f"当前数据库：{DATABASE_FILE}\n默认备份目录：{BACKUP_DIR}\n\n恢复前系统会自动创建一份安全备份。")
        backup = QPushButton("立即创建数据库备份"); restore = QPushButton("从备份文件恢复")
        backup.clicked.connect(self.backup); restore.clicked.connect(self.restore)
        layout.addWidget(title); layout.addWidget(info); layout.addWidget(backup); layout.addWidget(restore); layout.addStretch()

    def backup(self) -> None:
        try: path = create_backup()
        except (OSError, ValueError) as exc: QMessageBox.critical(self, "备份失败", str(exc)); return
        QMessageBox.information(self, "备份成功", f"备份已保存到：\n{path}")

    def restore(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, "选择数据库备份", str(BACKUP_DIR), "SQLite 数据库 (*.db)")
        if not filename: return
        if QMessageBox.question(self, "确认恢复", "恢复会替换当前数据库，确定继续吗？") != QMessageBox.StandardButton.Yes: return
        try: safety = restore_backup(Path(filename))
        except (OSError, ValueError) as exc: QMessageBox.critical(self, "恢复失败", str(exc)); return
        QMessageBox.information(self, "恢复成功", f"数据已恢复。恢复前的安全备份：\n{safety}\n请重新启动程序。")
