"""读者账户管理页面。"""

from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from services.reader_service import (
    activate_reader, add_reader, deactivate_reader, list_readers, reset_reader_password, update_reader,
)


class ReaderDialog(QDialog):
    def __init__(self, reader: dict | None = None, parent=None) -> None:
        super().__init__(parent); self.reader = reader
        self.setWindowTitle("编辑读者" if reader else "新增读者")
        self.username = QLineEdit((reader or {}).get("username", "")); self.username.setReadOnly(reader is not None)
        self.password = QLineEdit(); self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.name = QLineEdit((reader or {}).get("real_name", ""))
        self.phone = QLineEdit((reader or {}).get("phone") or "")
        form = QFormLayout(self); form.addRow("用户名", self.username)
        if reader is None: form.addRow("初始密码", self.password)
        form.addRow("姓名", self.name); form.addRow("电话", self.phone)
        buttons = QHBoxLayout(); save = QPushButton("保存"); cancel = QPushButton("取消")
        save.clicked.connect(self.accept); cancel.clicked.connect(self.reject)
        buttons.addWidget(save); buttons.addWidget(cancel); form.addRow(buttons)


class ResetPasswordDialog(QDialog):
    def __init__(self, reader: dict, parent=None) -> None:
        super().__init__(parent); self.setWindowTitle("重置读者密码")
        self.password = QLineEdit(); self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm = QLineEdit(); self.confirm.setEchoMode(QLineEdit.EchoMode.Password)
        form = QFormLayout(self); form.addRow("读者", QLabel(f"{reader['real_name']}（{reader['username']}）"))
        form.addRow("新临时密码", self.password); form.addRow("确认密码", self.confirm)
        buttons = QHBoxLayout(); save = QPushButton("确认重置"); cancel = QPushButton("取消")
        save.clicked.connect(self.validate_and_accept); cancel.clicked.connect(self.reject)
        buttons.addWidget(save); buttons.addWidget(cancel); form.addRow(buttons)

    def validate_and_accept(self) -> None:
        if self.password.text() != self.confirm.text():
            QMessageBox.warning(self, "输入错误", "两次输入的密码不一致"); return
        if len(self.password.text()) < 6:
            QMessageBox.warning(self, "输入错误", "新密码至少需要 6 位"); return
        self.accept()


class ReadersPage(QWidget):
    def __init__(self, operator_id: int | None = None, parent=None) -> None:
        super().__init__(parent); self.operator_id = operator_id; self.rows: list[dict] = []
        self.search = QLineEdit(); self.search.setPlaceholderText("按用户名、姓名或电话搜索")
        self.show_inactive = QCheckBox("显示停用")
        query = QPushButton("查询"); add = QPushButton("新增读者"); edit = QPushButton("编辑")
        reset = QPushButton("重置密码"); disable = QPushButton("启用/停用")
        bar = QHBoxLayout(); bar.addWidget(self.search, 1)
        bar.addWidget(self.show_inactive)
        for button in (query, add, edit, reset, disable): bar.addWidget(button)
        self.table = QTableWidget(0, 6); self.table.setHorizontalHeaderLabels(["ID", "用户名", "姓名", "电话", "状态", "创建时间"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); self.table.horizontalHeader().setStretchLastSection(True)
        layout = QVBoxLayout(self); title = QLabel("读者管理"); title.setObjectName("pageTitle")
        layout.addWidget(title); layout.addLayout(bar); layout.addWidget(self.table)
        query.clicked.connect(self.refresh); self.search.returnPressed.connect(self.refresh)
        add.clicked.connect(self.add_item); edit.clicked.connect(self.edit_item)
        reset.clicked.connect(self.reset_password); disable.clicked.connect(self.toggle_active)
        self.show_inactive.toggled.connect(self.refresh); self.refresh()

    def refresh(self) -> None:
        self.rows = list_readers(self.search.text(), self.show_inactive.isChecked()); self.table.setRowCount(len(self.rows))
        for row, reader in enumerate(self.rows):
            values = (reader["id"], reader["username"], reader["real_name"], reader["phone"] or "", "正常" if reader["status"] else "停用", reader["created_at"])
            for column, value in enumerate(values): self.table.setItem(row, column, QTableWidgetItem(str(value)))
        self.table.resizeColumnsToContents()

    def selected(self) -> dict | None:
        row = self.table.currentRow()
        if row < 0: QMessageBox.information(self, "提示", "请先选择一行"); return None
        return self.rows[row]

    def add_item(self) -> None:
        dialog = ReaderDialog(parent=self)
        if dialog.exec():
            try: add_reader(dialog.username.text(), dialog.password.text(), dialog.name.text(), dialog.phone.text(), self.operator_id); self.refresh()
            except ValueError as exc: QMessageBox.warning(self, "保存失败", str(exc))

    def edit_item(self) -> None:
        reader = self.selected()
        if not reader: return
        dialog = ReaderDialog(reader, self)
        if dialog.exec():
            try: update_reader(reader["id"], real_name=dialog.name.text(), phone=dialog.phone.text(), operator_id=self.operator_id); self.refresh()
            except ValueError as exc: QMessageBox.warning(self, "保存失败", str(exc))

    def reset_password(self) -> None:
        reader = self.selected()
        if not reader: return
        dialog = ResetPasswordDialog(reader, self)
        if dialog.exec():
            try: reset_reader_password(reader["id"], dialog.password.text(), self.operator_id)
            except ValueError as exc: QMessageBox.warning(self, "重置失败", str(exc)); return
            QMessageBox.information(self, "重置成功", "读者密码已重置，请通知读者登录后立即修改密码。")

    def toggle_active(self) -> None:
        reader = self.selected()
        if not reader: return
        action = "停用" if reader["status"] else "启用"
        if QMessageBox.question(self, "确认", f"确定{action}读者“{reader['real_name']}”吗？") == QMessageBox.StandardButton.Yes:
            try:
                if reader["status"]: deactivate_reader(reader["id"], operator_id=self.operator_id)
                else: activate_reader(reader["id"], operator_id=self.operator_id)
                self.refresh()
            except ValueError as exc: QMessageBox.warning(self, "操作失败", str(exc))
