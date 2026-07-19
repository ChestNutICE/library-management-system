"""管理员子账号与权限配置。"""

from PySide6.QtWidgets import QCheckBox,QDialog,QFormLayout,QHBoxLayout,QLabel,QLineEdit,QMessageBox,QPushButton,QTableWidget,QTableWidgetItem,QVBoxLayout,QWidget
from services.permission_service import PERMISSION_KEYS,add_staff,list_staff,update_permissions

LABELS=("图书管理","读者管理","借阅办理","报表与日志")
class StaffDialog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent);self.setWindowTitle("新增管理员子账号");self.username=QLineEdit();self.password=QLineEdit();self.password.setEchoMode(QLineEdit.EchoMode.Password);self.name=QLineEdit();self.checks=[QCheckBox(label) for label in LABELS]
        form=QFormLayout(self);form.addRow("用户名",self.username);form.addRow("密码",self.password);form.addRow("姓名",self.name)
        for box in self.checks:form.addRow(box)
        save=QPushButton("保存");save.clicked.connect(self.accept);form.addRow(save)
    def permissions(self):return {key:box.isChecked() for key,box in zip(PERMISSION_KEYS,self.checks)}

class PermissionsPage(QWidget):
    def __init__(self,operator_id:int,parent=None):
        super().__init__(parent);self.operator_id=operator_id;self.rows=[];self.table=QTableWidget(0,7);self.table.setHorizontalHeaderLabels(["ID","用户名","姓名",*LABELS]);self.table.horizontalHeader().setStretchLastSection(True)
        add=QPushButton("新增管理员子账号");save=QPushButton("保存选中账号权限");bar=QHBoxLayout();bar.addWidget(add);bar.addWidget(save);bar.addStretch()
        layout=QVBoxLayout(self);title=QLabel("管理员权限");title.setObjectName("pageTitle");layout.addWidget(title);layout.addLayout(bar);layout.addWidget(self.table)
        add.clicked.connect(self.add);save.clicked.connect(self.save);self.refresh()
    def refresh(self):
        self.rows=list_staff();self.table.setRowCount(len(self.rows))
        for row,item in enumerate(self.rows):
            for column,value in enumerate((item["id"],item["username"],item["real_name"])):self.table.setItem(row,column,QTableWidgetItem(str(value)))
            for offset,key in enumerate(PERMISSION_KEYS,3):box=QCheckBox();box.setChecked(bool(item[key]));self.table.setCellWidget(row,offset,box)
    def add(self):
        dialog=StaffDialog(self)
        if dialog.exec():
            try:add_staff(dialog.username.text(),dialog.password.text(),dialog.name.text(),dialog.permissions(),self.operator_id);self.refresh()
            except ValueError as exc:QMessageBox.warning(self,"新增失败",str(exc))
    def save(self):
        row=self.table.currentRow()
        if row<0:QMessageBox.information(self,"提示","请先选择账号");return
        permissions={key:self.table.cellWidget(row,index+3).isChecked() for index,key in enumerate(PERMISSION_KEYS)}
        try:update_permissions(self.rows[row]["id"],permissions,self.operator_id);QMessageBox.information(self,"成功","权限已更新，该账号重新登录后生效。")
        except ValueError as exc:QMessageBox.warning(self,"保存失败",str(exc))
