# 图书管理系统

基于 Python、PySide6 和 SQLite 的单机桌面图书管理系统。

## 运行

```powershell
.\.venv312\Scripts\python.exe main.py
```

初始管理员：`admin`，初始密码：`admin123`。

## 测试

```powershell
.\.venv312\Scripts\python.exe -m pytest -q
```

## 目录职责

- `database/`：数据库连接、事务、建表和初始化。
- `models/`：数据模型。
- `services/`：业务规则。
- `views/`：PySide6界面。
- `utils/`：密码、日期、校验和路径工具。
- `assets/`：样式和图标资源。
- `tests/`：自动测试。
- `docs/`：软件工程文档。
