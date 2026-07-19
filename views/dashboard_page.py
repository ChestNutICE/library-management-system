"""实时统计首页。"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QGroupBox, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from models.user import User
from services.loan_service import list_loans
from services.statistics_service import dashboard_counts, popular_books


class DashboardPage(QWidget):
    def __init__(self, user: User, view_reports: bool | None = None, parent=None) -> None:
        super().__init__(parent); self.user = user; self.view_reports = user.role == "admin" if view_reports is None else view_reports; self.value_labels: dict[str, QLabel] = {}
        layout = QVBoxLayout(self); header = QGridLayout()
        title = QLabel(f"欢迎，{user.real_name}"); title.setObjectName("pageTitle")
        refresh = QPushButton("刷新统计"); refresh.clicked.connect(self.refresh)
        header.addWidget(title, 0, 0); header.addWidget(refresh, 0, 1, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addLayout(header)
        cards = QGridLayout()
        labels = (("book_titles", "图书种类"), ("total_copies", "馆藏总量"),
                  ("readers", "有效读者"), ("borrowed", "当前在借"), ("overdue", "当前逾期"))
        for column, (key, text) in enumerate(labels):
            box = QGroupBox(text); box_layout = QVBoxLayout(box); value = QLabel("0")
            value.setAlignment(Qt.AlignmentFlag.AlignCenter); value.setStyleSheet("font-size: 28px; font-weight: bold; color: #2e74b5;")
            box_layout.addWidget(value); cards.addWidget(box, 0, column); self.value_labels[key] = value
        layout.addLayout(cards)
        subtitle = QLabel("热门图书（按累计借阅次数）"); subtitle.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.table = QTableWidget(0, 4); self.table.setHorizontalHeaderLabels(["排名", "书名", "作者", "借阅次数"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(subtitle); layout.addWidget(self.table); self.refresh()

    def refresh(self) -> None:
        if self.view_reports:
            counts = dashboard_counts()
        else:
            own = list_loans(user_id=self.user.id)
            counts = {"book_titles": 0, "total_copies": 0, "readers": 0,
                      "borrowed": sum(x["status"] in ("borrowed", "overdue") for x in own),
                      "overdue": sum(x["status"] == "overdue" for x in own)}
        for key, label in self.value_labels.items():
            label.setText("—" if not self.view_reports and key in ("book_titles", "total_copies", "readers") else str(counts[key]))
        books = popular_books(); self.table.setRowCount(len(books))
        for row, book in enumerate(books):
            for column, value in enumerate((row + 1, book["title"], book["author"], book["loan_count"])):
                self.table.setItem(row, column, QTableWidgetItem(str(value)))
        self.table.resizeColumnsToContents()
