"""统一管理项目路径。"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_FILE = DATA_DIR / "library.db"
ASSETS_DIR = PROJECT_ROOT / "assets"


def asset_path(name: str) -> Path:
    return ASSETS_DIR / name
