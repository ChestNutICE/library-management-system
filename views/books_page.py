"""图书管理、分类筛选、封面和条码枪快速查询页面。"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QDialog,
    QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from services.book_service import activate_book, add_book, deactivate_book, list_books, update_book
from services.category_service import list_categories


class BookDialog(QDialog):
    def __init__(self, book: dict | None = None, parent=None) -> None:
        super().__init__(parent); self.setWindowTitle("编辑图书" if book else "新增图书")
        self.isbn = QLineEdit(book["isbn"] if book else ""); self.isbn.setReadOnly(book is not None)
        self.title_edit = QLineEdit((book or {}).get("title", "")); self.author = QLineEdit((book or {}).get("author", ""))
        self.publisher = QLineEdit((book or {}).get("publisher") or ""); self.location = QLineEdit((book or {}).get("location") or "")
        self.count = QSpinBox(); self.count.setRange(0, 99999); self.count.setValue((book or {}).get("total_count", 1))
        self.category = QComboBox(); self.category.addItem("未分类", None)
        for row in list_categories(): self.category.addItem(row["name"], row["id"])
        index = self.category.findData((book or {}).get("category_id")); self.category.setCurrentIndex(max(index, 0))
        self.cover = QLineEdit((book or {}).get("cover_path") or ""); choose = QPushButton("选择图片"); choose.clicked.connect(self.choose_cover)
        self.preview=QLabel("无封面");self.preview.setFixedSize(120,160);self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter);self.preview.setStyleSheet("border:1px solid #afc0ce;background:white;")
        cover_row = QHBoxLayout(); cover_row.addWidget(self.cover, 1); cover_row.addWidget(choose)
        form = QFormLayout(self)
        for label, widget in (("ISBN",self.isbn),("书名",self.title_edit),("作者",self.author),("出版社",self.publisher),("分类",self.category),("馆藏位置",self.location),("总库存",self.count)): form.addRow(label,widget)
        form.addRow("封面图片", cover_row);form.addRow("预览",self.preview);self.update_preview()
        buttons = QHBoxLayout(); save=QPushButton("保存"); cancel=QPushButton("取消"); save.clicked.connect(self.accept); cancel.clicked.connect(self.reject)
        buttons.addWidget(save); buttons.addWidget(cancel); form.addRow(buttons)

    def choose_cover(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, "选择封面", "", "图片 (*.png *.jpg *.jpeg *.bmp)")
        if filename: self.cover.setText(filename);self.update_preview()

    def update_preview(self) -> None:
        pixmap=QPixmap(self.cover.text())
        if pixmap.isNull():self.preview.setText("无封面")
        else:self.preview.setPixmap(pixmap.scaled(self.preview.size(),Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))

    def values(self) -> dict:
        return {"isbn":self.isbn.text(),"title":self.title_edit.text(),"author":self.author.text(),"publisher":self.publisher.text(),"category_id":self.category.currentData(),"location":self.location.text(),"total_count":self.count.value(),"cover_path":self.cover.text()}


class BooksPage(QWidget):
    def __init__(self, can_manage=True, operator_id=None, parent=None) -> None:
        super().__init__(parent); self.operator_id=operator_id; self.can_manage=can_manage; self.rows=[]
        self.search=QLineEdit(); self.search.setPlaceholderText("书名、作者、ISBN，条码枪扫描后按回车")
        self.category=QComboBox(); self.category.addItem("全部分类",None)
        for row in list_categories(): self.category.addItem(row["name"],row["id"])
        self.inactive=QCheckBox("显示停用"); query=QPushButton("查询"); add=QPushButton("新增"); edit=QPushButton("编辑"); toggle=QPushButton("启用/停用")
        bar=QHBoxLayout(); bar.addWidget(self.search,1); bar.addWidget(self.category); bar.addWidget(self.inactive); bar.addWidget(query)
        if can_manage:
            for button in (add,edit,toggle): bar.addWidget(button)
        self.table=QTableWidget(0,10); self.table.setHorizontalHeaderLabels(["ID","ISBN","书名","作者","分类","出版社","总数","可借","位置","状态"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); self.table.horizontalHeader().setStretchLastSection(True)
        layout=QVBoxLayout(self); title=QLabel("图书管理" if can_manage else "图书查询"); title.setObjectName("pageTitle"); layout.addWidget(title); layout.addLayout(bar); layout.addWidget(self.table)
        query.clicked.connect(self.refresh); self.search.returnPressed.connect(self.refresh); self.category.currentIndexChanged.connect(self.refresh); self.inactive.toggled.connect(self.refresh)
        if can_manage: add.clicked.connect(self.add_item); edit.clicked.connect(self.edit_item); toggle.clicked.connect(self.toggle_item)
        self.refresh()

    def refresh(self) -> None:
        self.rows=list_books(self.search.text(),self.inactive.isChecked(),self.category.currentData()); self.table.setRowCount(len(self.rows))
        for row,book in enumerate(self.rows):
            values=(book["id"],book["isbn"],book["title"],book["author"],book["category_name"] or "",book["publisher"] or "",book["total_count"],book["available_count"],book["location"] or "","正常" if book["status"] else "停用")
            for column,value in enumerate(values): self.table.setItem(row,column,QTableWidgetItem(str(value)))
        self.table.resizeColumnsToContents()

    def selected(self):
        row=self.table.currentRow()
        if row<0: QMessageBox.information(self,"提示","请先选择一行"); return None
        return self.rows[row]

    def add_item(self):
        dialog=BookDialog(parent=self)
        if dialog.exec():
            try: add_book(**dialog.values(),operator_id=self.operator_id); self.refresh()
            except ValueError as exc: QMessageBox.warning(self,"保存失败",str(exc))

    def edit_item(self):
        book=self.selected()
        if not book:return
        dialog=BookDialog(book,self)
        if dialog.exec():
            values=dialog.values(); values.pop("isbn")
            try:update_book(book["id"],**values,operator_id=self.operator_id);self.refresh()
            except ValueError as exc:QMessageBox.warning(self,"保存失败",str(exc))

    def toggle_item(self):
        book=self.selected()
        if not book:return
        try:
            if book["status"]: deactivate_book(book["id"],self.operator_id)
            else: activate_book(book["id"],self.operator_id)
            self.refresh()
        except ValueError as exc: QMessageBox.warning(self,"操作失败",str(exc))
