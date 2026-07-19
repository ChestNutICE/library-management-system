"""即将到期和逾期提醒。"""

from PySide6.QtWidgets import QLabel, QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QHBoxLayout, QWidget

from models.user import User
from services.reminder_service import due_reminders


class RemindersPage(QWidget):
    def __init__(self, user: User, view_all: bool | None = None, parent=None) -> None:
        super().__init__(parent); self.user=user; self.view_all=user.role=="admin" if view_all is None else view_all
        self.days=QSpinBox(); self.days.setRange(1,30); self.days.setValue(3)
        refresh=QPushButton("刷新"); bar=QHBoxLayout(); bar.addWidget(QLabel("提前提醒天数")); bar.addWidget(self.days); bar.addWidget(refresh); bar.addStretch()
        self.table=QTableWidget(0,6); self.table.setHorizontalHeaderLabels(["读者","图书","应还日期","剩余天数","状态","联系电话"]); self.table.horizontalHeader().setStretchLastSection(True)
        layout=QVBoxLayout(self); title=QLabel("到期提醒"); title.setObjectName("pageTitle"); layout.addWidget(title); layout.addLayout(bar); layout.addWidget(self.table)
        refresh.clicked.connect(self.refresh); self.days.valueChanged.connect(self.refresh); self.refresh()

    def refresh(self) -> None:
        user_id=None if self.view_all else self.user.id
        rows=due_reminders(self.days.value(),user_id); self.table.setRowCount(len(rows))
        for row,item in enumerate(rows):
            remaining=item["days_remaining"]; state="已逾期" if remaining<0 else ("今天到期" if remaining==0 else "即将到期")
            values=(item["real_name"],item["title"],item["due_date"],remaining,state,item["phone"] or "")
            for column,value in enumerate(values):self.table.setItem(row,column,QTableWidgetItem(str(value)))
        self.table.resizeColumnsToContents()
