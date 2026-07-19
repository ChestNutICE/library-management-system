"""登录窗口。"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from services.auth_service import authenticate
from views.main_window import MainWindow


class LoginWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.main_window: MainWindow | None = None
        self.setWindowTitle("图书管理系统 - 登录")
        self.setFixedSize(420, 360)

        title = QLabel("图书管理系统")
        title.setObjectName("pageTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("用户名")
        self.username_input.setText("admin")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("密码")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        login_button = QPushButton("登录")
        login_button.clicked.connect(self.login)
        self.password_input.returnPressed.connect(self.login)

        hint = QLabel("初始管理员：admin / admin123")
        hint.setObjectName("hint")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout()
        layout.setContentsMargins(48, 45, 48, 45)
        layout.setSpacing(18)
        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(login_button)
        layout.addWidget(hint)

        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)

    def login(self) -> None:
        user = authenticate(self.username_input.text(), self.password_input.text())
        if user is None:
            QMessageBox.warning(self, "登录失败", "用户名、密码错误或账户已停用。")
            return
        self.main_window = MainWindow(user)
        self.main_window.show()
        self.close()
