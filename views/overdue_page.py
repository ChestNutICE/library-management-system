"""逾期借阅记录页面。"""

from datetime import date

from PySide6.QtWidgets import QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from models.user import User
from services.loan_service import list_loans


class OverduePage(QWidget):
    def __init__(self, user: User, parent=None) -> None:
        super().__init__(parent); self.user = user
        layout = QVBoxLayout(self); title = QLabel("逾期记录"); title.setObjectName("pageTitle")
        refresh = QPushButton("刷新逾期记录"); refresh.clicked.connect(self.refresh)
        self.table = QTableWidget(0, 7); self.table.setHorizontalHeaderLabels(["记录ID", "读者", "图书", "ISBN", "应还日期", "逾期天数", "预计费用"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(title); layout.addWidget(refresh); layout.addWidget(self.table); self.refresh()

    def refresh(self) -> None:
        user_id = self.user.id if self.user.role == "reader" else None
        rows = list_loans(status="overdue", user_id=user_id); self.table.setRowCount(len(rows))
        for row, loan in enumerate(rows):
            days = max(0, (date.today() - date.fromisoformat(loan["due_date"])).days)
            values = (loan["id"], loan["real_name"], loan["title"], loan["isbn"], loan["due_date"], days, f"{days * 0.5:.2f}")
            for column, value in enumerate(values): self.table.setItem(row, column, QTableWidgetItem(str(value)))
        self.table.resizeColumnsToContents()
