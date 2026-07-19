"""主窗口和细粒度权限导航。"""
from PySide6.QtWidgets import QMainWindow,QTabWidget
from models.user import User
from services.permission_service import get_permissions
from views.account_page import AccountPage
from views.books_page import BooksPage
from views.categories_page import CategoriesPage
from views.dashboard_page import DashboardPage
from views.data_page import DataPage
from views.loans_page import LoansPage
from views.logs_page import LogsPage
from views.overdue_page import OverduePage
from views.permissions_page import PermissionsPage
from views.readers_page import ReadersPage
from views.reminders_page import RemindersPage

class MainWindow(QMainWindow):
    def __init__(self,user:User)->None:
        super().__init__();self.user=user;permissions=get_permissions(user.id) if user.role=="admin" else {"manage_books":False,"manage_readers":False,"manage_loans":False,"view_reports":False}
        self.setWindowTitle("图书管理系统");self.resize(1180,760);self.tabs=QTabWidget();self.tabs.addTab(DashboardPage(user,permissions["view_reports"]),"首页")
        self.tabs.addTab(BooksPage(permissions["manage_books"],user.id),"图书管理" if permissions["manage_books"] else "图书查询")
        if permissions["manage_books"]:self.tabs.addTab(CategoriesPage(user.id),"图书分类")
        if permissions["manage_readers"]:self.tabs.addTab(ReadersPage(user.id),"读者管理")
        self.tabs.addTab(LoansPage(user,permissions["manage_loans"]),"借阅管理")
        self.tabs.addTab(OverduePage(user,permissions["view_reports"]),"逾期记录");self.tabs.addTab(RemindersPage(user,permissions["view_reports"]),"到期提醒")
        if permissions["view_reports"]:self.tabs.addTab(LogsPage(),"操作日志");self.tabs.addTab(DataPage(user.id),"数据维护")
        if user.username=="admin":self.tabs.addTab(PermissionsPage(user.id),"管理员权限")
        self.tabs.addTab(AccountPage(user),"账户设置");self.tabs.currentChanged.connect(self._refresh_current);self.setCentralWidget(self.tabs);self.statusBar().showMessage(f"当前用户：{user.real_name}（{user.role}）")
    def _refresh_current(self,index:int)->None:
        refresh=getattr(self.tabs.widget(index),"refresh",None)
        if callable(refresh):refresh()
