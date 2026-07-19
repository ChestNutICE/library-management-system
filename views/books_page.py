"""图书资料管理页面。"""

from PySide6.QtWidgets import (
    QAbstractItemView, QDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QSpinBox, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from services.book_service import add_book, deactivate_book, list_books, update_book


class BookDialog(QDialog):
    def __init__(self, book: dict | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("编辑图书" if book else "新增图书")
        self.isbn = QLineEdit(book["isbn"] if book else "")
        self.isbn.setReadOnly(book is not None)
        self.title_edit = QLineEdit(book["title"] if book else "")
        self.author = QLineEdit(book["author"] if book else "")
        self.publisher = QLineEdit((book or {}).get("publisher") or "")
        self.location = QLineEdit((book or {}).get("location") or "")
        self.count = QSpinBox(); self.count.setRange(0, 99999)
        self.count.setValue((book or {}).get("total_count", 1))
        form = QFormLayout(self)
        for label, widget in (("ISBN", self.isbn), ("书名", self.title_edit),
                              ("作者", self.author), ("出版社", self.publisher),
                              ("馆藏位置", self.location), ("总库存", self.count)):
            form.addRow(label, widget)
        buttons = QHBoxLayout()
        save = QPushButton("保存"); cancel = QPushButton("取消")
        save.clicked.connect(self.accept); cancel.clicked.connect(self.reject)
        buttons.addWidget(save); buttons.addWidget(cancel); form.addRow(buttons)

    def values(self) -> dict:
        return {"isbn": self.isbn.text(), "title": self.title_edit.text(),
                "author": self.author.text(), "publisher": self.publisher.text(),
                "location": self.location.text(), "total_count": self.count.value()}


class BooksPage(QWidget):
    def __init__(self, can_manage: bool = True, operator_id: int | None = None, parent=None) -> None:
        super().__init__(parent)
        self.operator_id = operator_id
        self.search = QLineEdit(); self.search.setPlaceholderText("按 ISBN、书名或作者搜索")
        search_button = QPushButton("查询"); add_button = QPushButton("新增图书")
        edit_button = QPushButton("编辑"); disable_button = QPushButton("停用")
        bar = QHBoxLayout(); bar.addWidget(self.search, 1)
        bar.addWidget(search_button)
        if can_manage:
            for button in (add_button, edit_button, disable_button): bar.addWidget(button)
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["ID", "ISBN", "书名", "作者", "出版社", "总数", "可借", "位置"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout = QVBoxLayout(self); title = QLabel("图书管理"); title.setObjectName("pageTitle")
        layout.addWidget(title); layout.addLayout(bar); layout.addWidget(self.table)
        search_button.clicked.connect(self.refresh); self.search.returnPressed.connect(self.refresh)
        if can_manage:
            add_button.clicked.connect(self.add_item); edit_button.clicked.connect(self.edit_item)
            disable_button.clicked.connect(self.disable_item)
        self.refresh()

    def refresh(self) -> None:
        books = list_books(self.search.text())
        self.table.setRowCount(len(books))
        for row, book in enumerate(books):
            self.table.setItem(row, 0, QTableWidgetItem(str(book["id"])))
            for column, key in enumerate(("isbn", "title", "author", "publisher", "total_count", "available_count", "location"), 1):
                self.table.setItem(row, column, QTableWidgetItem(str(book[key] or "")))
        self.table.resizeColumnsToContents()

    def selected(self) -> dict | None:
        row = self.table.currentRow()
        if row < 0: QMessageBox.information(self, "提示", "请先选择一行"); return None
        return list_books(self.search.text())[row]

    def add_item(self) -> None:
        dialog = BookDialog(parent=self)
        if dialog.exec():
            try: add_book(**dialog.values(), operator_id=self.operator_id); self.refresh()
            except ValueError as exc: QMessageBox.warning(self, "保存失败", str(exc))

    def edit_item(self) -> None:
        book = self.selected()
        if not book: return
        dialog = BookDialog(book, self)
        if dialog.exec():
            values = dialog.values(); values.pop("isbn")
            try: update_book(book["id"], **values, operator_id=self.operator_id); self.refresh()
            except ValueError as exc: QMessageBox.warning(self, "保存失败", str(exc))

    def disable_item(self) -> None:
        book = self.selected()
        if book and QMessageBox.question(self, "确认", f"确定停用《{book['title']}》吗？") == QMessageBox.StandardButton.Yes:
            deactivate_book(book["id"], operator_id=self.operator_id); self.refresh()
