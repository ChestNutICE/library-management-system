"""日期计算工具。"""

from datetime import date, timedelta

from config import BORROW_DAYS


def today() -> date:
    return date.today()


def default_due_date(borrow_date: date | None = None) -> date:
    return (borrow_date or today()) + timedelta(days=BORROW_DAYS)
