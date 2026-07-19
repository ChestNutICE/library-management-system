"""主窗口和按角色显示的业务导航。"""

from PySide6.QtWidgets import QMainWindow, QTabWidget

from models.user import User
from views.account_page import AccountPage
from views.books_page import BooksPage
from views.dashboard_page import DashboardPage
from views.data_page import DataPage
from views.loans_page import LoansPage
from views.logs_page import LogsPage
from views.overdue_page import OverduePage
from views.readers_page import ReadersPage


class MainWindow(QMainWindow):
    def __init__(self, user: User) -> None:
        super().__init__(); self.user = user
        self.setWindowTitle("图书管理系统"); self.resize(1100, 720)
        self.tabs = QTabWidget(); self.tabs.addTab(DashboardPage(user), "首页")
        self.tabs.addTab(BooksPage(can_manage=user.role == "admin", operator_id=user.id), "图书查询" if user.role == "reader" else "图书管理")
        if user.role == "admin": self.tabs.addTab(ReadersPage(operator_id=user.id), "读者管理")
        self.tabs.addTab(LoansPage(user), "借阅管理")
        self.tabs.addTab(OverduePage(user), "逾期记录")
        if user.role == "admin": self.tabs.addTab(LogsPage(), "操作日志")
        if user.role == "admin": self.tabs.addTab(DataPage(), "数据维护")
        self.tabs.addTab(AccountPage(user), "账户设置")
        self.tabs.currentChanged.connect(self._refresh_current)
        self.setCentralWidget(self.tabs); self.statusBar().showMessage(f"当前用户：{user.real_name}（{user.role}）")

    def _refresh_current(self, index: int) -> None:
        page = self.tabs.widget(index)
        refresh = getattr(page, "refresh", None)
        if callable(refresh): refresh()
