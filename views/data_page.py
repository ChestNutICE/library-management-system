"""管理员备份、恢复、Excel 数据交换和 PDF 报表页面。"""

from pathlib import Path
from PySide6.QtWidgets import QFileDialog, QGridLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget
from services.backup_service import create_backup, restore_backup
from services.export_service import export_books, export_dashboard_pdf, export_readers, import_books, import_readers
from utils.paths import BACKUP_DIR, DATABASE_FILE


class DataPage(QWidget):
    def __init__(self, operator_id: int, parent=None) -> None:
        super().__init__(parent); self.operator_id=operator_id
        layout=QVBoxLayout(self); title=QLabel("数据维护与报表"); title.setObjectName("pageTitle")
        info=QLabel(f"当前数据库：{DATABASE_FILE}\n默认备份目录：{BACKUP_DIR}\n恢复前会自动创建安全备份；导入读者的默认密码为 123456。")
        grid=QGridLayout(); actions=(("创建数据库备份",self.backup),("从备份恢复",self.restore),("导出图书 Excel",self.export_books),("导入图书 Excel",self.import_books),("导出读者 Excel",self.export_readers),("导入读者 Excel",self.import_readers),("导出统计 PDF",self.export_pdf))
        for index,(text,slot) in enumerate(actions): button=QPushButton(text);button.clicked.connect(slot);grid.addWidget(button,index//2,index%2)
        layout.addWidget(title);layout.addWidget(info);layout.addLayout(grid);layout.addStretch()

    def backup(self):
        try:path=create_backup()
        except (OSError,ValueError) as exc:QMessageBox.critical(self,"备份失败",str(exc));return
        QMessageBox.information(self,"备份成功",f"已保存到：\n{path}")

    def restore(self):
        filename,_=QFileDialog.getOpenFileName(self,"选择数据库备份",str(BACKUP_DIR),"SQLite 数据库 (*.db)")
        if not filename or QMessageBox.question(self,"确认恢复","恢复会替换当前数据库，确定继续吗？")!=QMessageBox.StandardButton.Yes:return
        try:safety=restore_backup(Path(filename))
        except (OSError,ValueError) as exc:QMessageBox.critical(self,"恢复失败",str(exc));return
        QMessageBox.information(self,"恢复成功",f"恢复前安全备份：\n{safety}\n请重启程序。")

    def _save(self,title,pattern,callback):
        filename,_=QFileDialog.getSaveFileName(self,title,"",pattern)
        if filename:
            try:callback(Path(filename));QMessageBox.information(self,"成功",f"文件已保存：\n{filename}")
            except Exception as exc:QMessageBox.critical(self,"操作失败",str(exc))

    def _import(self,title,callback):
        filename,_=QFileDialog.getOpenFileName(self,title,"","Excel 工作簿 (*.xlsx)")
        if filename:
            try:success,errors=callback(Path(filename),self.operator_id)
            except Exception as exc:QMessageBox.critical(self,"导入失败",str(exc));return
            detail="\n".join(errors[:10]);QMessageBox.information(self,"导入完成",f"成功 {success} 条，失败 {len(errors)} 条。\n{detail}")

    def export_books(self):self._save("导出图书","Excel 工作簿 (*.xlsx)",export_books)
    def export_readers(self):self._save("导出读者","Excel 工作簿 (*.xlsx)",export_readers)
    def export_pdf(self):self._save("导出统计报表","PDF 文件 (*.pdf)",export_dashboard_pdf)
    def import_books(self):self._import("导入图书",import_books)
    def import_readers(self):self._import("导入读者",import_readers)
