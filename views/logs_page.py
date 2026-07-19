"""管理员操作日志查询页面。"""

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from services.log_service import list_logs


ACTIONS = (
    ("全部操作", "all"), ("新增图书", "book.add"), ("修改图书", "book.update"),
    ("停用图书", "book.deactivate"), ("新增读者", "reader.add"),
    ("修改读者", "reader.update"), ("停用读者", "reader.deactivate"),
    ("办理借书", "loan.borrow"), ("办理还书", "loan.return"),
)
ACTION_TEXT = dict((value, text) for text, value in ACTIONS)


class LogsPage(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.search = QLineEdit(); self.search.setPlaceholderText("搜索操作者或操作详情")
        self.action = QComboBox()
        for text, value in ACTIONS: self.action.addItem(text, value)
        query = QPushButton("查询"); bar = QHBoxLayout(); bar.addWidget(self.search, 1); bar.addWidget(self.action); bar.addWidget(query)
        self.table = QTableWidget(0, 5); self.table.setHorizontalHeaderLabels(["ID", "操作者", "操作类型", "详情", "时间"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers); self.table.horizontalHeader().setStretchLastSection(True)
        layout = QVBoxLayout(self); title = QLabel("操作日志"); title.setObjectName("pageTitle")
        layout.addWidget(title); layout.addLayout(bar); layout.addWidget(self.table)
        query.clicked.connect(self.refresh); self.search.returnPressed.connect(self.refresh); self.action.currentIndexChanged.connect(self.refresh); self.refresh()

    def refresh(self) -> None:
        rows = list_logs(self.search.text(), self.action.currentData()); self.table.setRowCount(len(rows))
        for row, log in enumerate(rows):
            values = (log["id"], f"{log['real_name']} ({log['username']})", ACTION_TEXT.get(log["action"], log["action"]), log["details"] or "", log["created_at"])
            for column, value in enumerate(values): self.table.setItem(row, column, QTableWidgetItem(str(value)))
        self.table.resizeColumnsToContents()
