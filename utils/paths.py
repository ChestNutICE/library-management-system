"""统一管理项目路径。"""

from pathlib import Path
import sys

FROZEN = bool(getattr(sys, "frozen", False))
PROJECT_ROOT = Path(sys.executable).resolve().parent if FROZEN else Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_FILE = DATA_DIR / "library.db"
ASSETS_DIR = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT)) / "assets"
BACKUP_DIR = PROJECT_ROOT / "backups"


def asset_path(name: str) -> Path:
    return ASSETS_DIR / name
