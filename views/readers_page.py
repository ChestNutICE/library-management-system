"""读者账户管理页面。"""

from PySide6.QtWidgets import (QAbstractItemView, QDialog, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget)

from services.reader_service import add_reader, deactivate_reader, list_readers, update_reader


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


class ReadersPage(QWidget):
    def __init__(self, operator_id: int | None = None, parent=None) -> None:
        super().__init__(parent); self.operator_id = operator_id
        self.search = QLineEdit(); self.search.setPlaceholderText("按用户名、姓名或电话搜索")
        query = QPushButton("查询"); add = QPushButton("新增读者"); edit = QPushButton("编辑"); disable = QPushButton("停用")
        bar = QHBoxLayout(); bar.addWidget(self.search, 1)
        for button in (query, add, edit, disable): bar.addWidget(button)
        self.table = QTableWidget(0, 6); self.table.setHorizontalHeaderLabels(["ID", "用户名", "姓名", "电话", "状态", "创建时间"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); self.table.horizontalHeader().setStretchLastSection(True)
        layout = QVBoxLayout(self); title = QLabel("读者管理"); title.setObjectName("pageTitle")
        layout.addWidget(title); layout.addLayout(bar); layout.addWidget(self.table)
        query.clicked.connect(self.refresh); self.search.returnPressed.connect(self.refresh)
        add.clicked.connect(self.add_item); edit.clicked.connect(self.edit_item); disable.clicked.connect(self.disable_item); self.refresh()

    def refresh(self) -> None:
        readers = list_readers(self.search.text()); self.table.setRowCount(len(readers))
        for row, reader in enumerate(readers):
            values = (reader["id"], reader["username"], reader["real_name"], reader["phone"] or "", "正常" if reader["status"] else "停用", reader["created_at"])
            for column, value in enumerate(values): self.table.setItem(row, column, QTableWidgetItem(str(value)))
        self.table.resizeColumnsToContents()

    def selected(self) -> dict | None:
        row = self.table.currentRow()
        if row < 0: QMessageBox.information(self, "提示", "请先选择一行"); return None
        return list_readers(self.search.text())[row]

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

    def disable_item(self) -> None:
        reader = self.selected()
        if reader and QMessageBox.question(self, "确认", f"确定停用读者“{reader['real_name']}”吗？") == QMessageBox.StandardButton.Yes:
            try: deactivate_reader(reader["id"], operator_id=self.operator_id); self.refresh()
            except ValueError as exc: QMessageBox.warning(self, "无法停用", str(exc))
