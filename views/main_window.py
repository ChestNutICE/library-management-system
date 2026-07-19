"""主窗口骨架。"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

from models.user import User


class MainWindow(QMainWindow):
    def __init__(self, user: User) -> None:
        super().__init__()
        self.user = user
        self.setWindowTitle("图书管理系统")
        self.resize(1100, 720)

        title = QLabel("图书管理系统主窗口")
        title.setObjectName("pageTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome = QLabel(f"欢迎，{user.real_name}（{user.role}）")
        welcome.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout()
        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(welcome)
        layout.addStretch()
        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)
