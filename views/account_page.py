"""当前登录用户的密码修改页面。"""

from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget

from models.user import User
from services.auth_service import change_password


class AccountPage(QWidget):
    def __init__(self, user: User, parent=None) -> None:
        super().__init__(parent); self.user = user
        self.current = QLineEdit(); self.current.setEchoMode(QLineEdit.EchoMode.Password)
        self.new = QLineEdit(); self.new.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm = QLineEdit(); self.confirm.setEchoMode(QLineEdit.EchoMode.Password)
        form = QFormLayout(); form.addRow("用户名", QLabel(user.username)); form.addRow("原密码", self.current); form.addRow("新密码", self.new); form.addRow("确认新密码", self.confirm)
        save = QPushButton("修改密码"); save.clicked.connect(self.save)
        layout = QVBoxLayout(self); title = QLabel("账户设置"); title.setObjectName("pageTitle")
        layout.addWidget(title); layout.addLayout(form); layout.addWidget(save); layout.addStretch()

    def save(self) -> None:
        if self.new.text() != self.confirm.text():
            QMessageBox.warning(self, "修改失败", "两次输入的新密码不一致"); return
        try:
            change_password(self.user.id, self.current.text(), self.new.text())
        except ValueError as exc:
            QMessageBox.warning(self, "修改失败", str(exc)); return
        self.current.clear(); self.new.clear(); self.confirm.clear()
        QMessageBox.information(self, "成功", "密码已修改，下次登录请使用新密码")
