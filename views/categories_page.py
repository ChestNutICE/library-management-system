"""图书分类维护页面。"""

from PySide6.QtWidgets import QHBoxLayout, QInputDialog, QLabel, QMessageBox, QPushButton, QListWidget, QVBoxLayout, QWidget

from services.category_service import add_category, delete_category, list_categories, rename_category


class CategoriesPage(QWidget):
    def __init__(self, operator_id: int, parent=None) -> None:
        super().__init__(parent); self.operator_id = operator_id; self.rows = []
        self.list = QListWidget(); add = QPushButton("新增分类"); rename = QPushButton("重命名"); delete = QPushButton("删除")
        buttons = QHBoxLayout(); buttons.addWidget(add); buttons.addWidget(rename); buttons.addWidget(delete)
        layout = QVBoxLayout(self); title = QLabel("图书分类"); title.setObjectName("pageTitle")
        layout.addWidget(title); layout.addLayout(buttons); layout.addWidget(self.list)
        add.clicked.connect(self.add); rename.clicked.connect(self.rename); delete.clicked.connect(self.delete); self.refresh()

    def refresh(self) -> None:
        self.rows = list_categories(); self.list.clear(); self.list.addItems([row["name"] for row in self.rows])

    def selected(self):
        index = self.list.currentRow()
        if index < 0: QMessageBox.information(self, "提示", "请先选择一个分类"); return None
        return self.rows[index]

    def add(self) -> None:
        name, ok = QInputDialog.getText(self, "新增分类", "分类名称")
        if ok:
            try: add_category(name, self.operator_id); self.refresh()
            except ValueError as exc: QMessageBox.warning(self, "新增失败", str(exc))

    def rename(self) -> None:
        row = self.selected()
        if not row: return
        name, ok = QInputDialog.getText(self, "重命名分类", "新名称", text=row["name"])
        if ok:
            try: rename_category(row["id"], name, self.operator_id); self.refresh()
            except ValueError as exc: QMessageBox.warning(self, "修改失败", str(exc))

    def delete(self) -> None:
        row = self.selected()
        if row and QMessageBox.question(self, "确认", f"确定删除分类“{row['name']}”吗？") == QMessageBox.StandardButton.Yes:
            try: delete_category(row["id"], self.operator_id); self.refresh()
            except ValueError as exc: QMessageBox.warning(self, "删除失败", str(exc))
