"""借阅办理与记录查询页面。"""

from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget)

from models.user import User
from services.book_service import list_books
from services.loan_service import borrow_book, list_loans, return_book
from services.reader_service import list_readers


STATUS_TEXT = {"borrowed": "借阅中", "returned": "已归还", "overdue": "已逾期"}


class LoansPage(QWidget):
    def __init__(self, user: User, parent=None) -> None:
        super().__init__(parent); self.user = user; self.rows: list[dict] = []
        self.search = QLineEdit(); self.search.setPlaceholderText("按读者、书名或 ISBN 搜索")
        self.status = QComboBox(); self.status.addItem("全部状态", "all")
        for text, value in (("借阅中", "borrowed"), ("已逾期", "overdue"), ("已归还", "returned")): self.status.addItem(text, value)
        query = QPushButton("查询"); bar = QHBoxLayout(); bar.addWidget(self.search, 1); bar.addWidget(self.status); bar.addWidget(query)
        if user.role == "admin":
            self.reader = QComboBox(); self.book = QComboBox(); borrow = QPushButton("办理借书"); give_back = QPushButton("办理还书")
            action = QHBoxLayout(); action.addWidget(QLabel("读者")); action.addWidget(self.reader, 1); action.addWidget(QLabel("图书")); action.addWidget(self.book, 2); action.addWidget(borrow); action.addWidget(give_back)
            borrow.clicked.connect(self.borrow); give_back.clicked.connect(self.give_back)
        self.table = QTableWidget(0, 9); self.table.setHorizontalHeaderLabels(["记录ID", "读者", "图书", "借书日", "应还日", "归还日", "状态", "费用", "ISBN"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout = QVBoxLayout(self); title = QLabel("借阅管理"); title.setObjectName("pageTitle"); layout.addWidget(title)
        if user.role == "admin": layout.addLayout(action)
        layout.addLayout(bar); layout.addWidget(self.table)
        query.clicked.connect(self.refresh); self.search.returnPressed.connect(self.refresh); self.status.currentIndexChanged.connect(self.refresh)
        self.reload_options(); self.refresh()

    def reload_options(self) -> None:
        if self.user.role != "admin": return
        self.reader.clear(); self.book.clear()
        for reader in list_readers(): self.reader.addItem(f"{reader['real_name']} ({reader['username']})", reader["id"])
        for book in list_books():
            if book["available_count"] > 0: self.book.addItem(f"《{book['title']}》 可借 {book['available_count']}", book["id"])

    def refresh(self) -> None:
        user_id = self.user.id if self.user.role == "reader" else None
        self.rows = list_loans(self.search.text(), self.status.currentData(), user_id)
        self.table.setRowCount(len(self.rows))
        for row, loan in enumerate(self.rows):
            values = (loan["id"], loan["real_name"], loan["title"], loan["borrow_date"], loan["due_date"], loan["return_date"] or "", STATUS_TEXT[loan["status"]], f"{loan['fine']:.2f}", loan["isbn"])
            for column, value in enumerate(values): self.table.setItem(row, column, QTableWidgetItem(str(value)))
        self.table.resizeColumnsToContents()

    def borrow(self) -> None:
        if self.reader.currentData() is None or self.book.currentData() is None:
            QMessageBox.information(self, "提示", "请先创建可用读者和有库存的图书"); return
        try:
            borrow_book(self.reader.currentData(), self.book.currentData(), operator_id=self.user.id); QMessageBox.information(self, "成功", "借书办理完成")
            self.reload_options(); self.refresh()
        except ValueError as exc: QMessageBox.warning(self, "借书失败", str(exc))

    def give_back(self) -> None:
        row = self.table.currentRow()
        if row < 0: QMessageBox.information(self, "提示", "请先选择借阅记录"); return
        try:
            fine = return_book(self.rows[row]["id"], operator_id=self.user.id); QMessageBox.information(self, "成功", f"还书完成，逾期费用：{fine:.2f} 元")
            self.reload_options(); self.refresh()
        except ValueError as exc: QMessageBox.warning(self, "还书失败", str(exc))
